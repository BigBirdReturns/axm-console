"""axm — the operator command line. One seat for the whole ecosystem.

    axm surfaces                       list what you can capture or operate
    axm capture <surface> [-p k=v ...] drive a surface to a sealed, verified record
    axm operate <surface> [-p k=v ...] (alias of capture, for operation surfaces)
    axm verify <shard_dir> --key <pub> verify ANY sealed shard, print its receipt
    axm ask <shard_dir> --key <pub> [--sql "SELECT ..."] [question]
                                        verify-gated query of any sealed shard
    axm queue                          show your review queue
    axm review <shard_id> --by <name> --as <escalate|dismiss|needs_context> [--note ..]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .ask import ask, render_table
from .console import Console
from .surfaces import Status, all_surfaces


def _home() -> Path:
    return Path(os.environ.get("AXM_CONSOLE_HOME", Path.home() / ".axm-console"))


def _params(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise SystemExit(f"bad -p {p!r}; expected key=value")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def cmd_surfaces(_args) -> int:
    print("SURFACES — what you can capture or operate\n" + "─" * 60)
    for s in all_surfaces():
        mark = "▶ driven " if s.status is Status.DRIVEN else "· declared"
        print(f"  {mark}  {s.name:<20} {s.verb:<8} [{s.tier}]")
        print(f"              {s.summary}  ({s.owner_repo})")
    print("─" * 60)
    print("driven = the console runs it end to end here · declared = spoke proves it in its own repo")
    return 0


def _do_capture(args) -> int:
    console = Console(_home())
    try:
        receipt, _shard = console.run_surface(args.surface, params=_params(args.param))
    except NotImplementedError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    print(receipt.render())
    if receipt.verified:
        print("\nadmitted to your review queue.  run:  axm queue")
        if receipt.trusted_key_path:
            print(f"ask it:  axm ask {receipt.shard_dir} --key {receipt.trusted_key_path}")
    return 0 if receipt.verified else 1


def cmd_verify(args) -> int:
    console = Console(_home())
    receipt = console.verify_shard(args.shard_dir, args.key)
    print(receipt.render())
    return 0 if receipt.verified else 1


def cmd_ask(args) -> int:
    if not args.key:
        print("REFUSED: the console never queries an unverified shard; "
              "supply --key <out-of-band trusted public key>.", file=sys.stderr)
        return 2
    try:
        result = ask(args.shard_dir, args.key, sql=args.sql, question=args.question)
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    print(render_table(result["columns"], result["rows"], result["shard_id"]))
    return 0


def cmd_queue(_args) -> int:
    print(Console(_home()).queue.render())
    return 0


def cmd_review(args) -> int:
    try:
        Console(_home()).review(args.shard_id, reviewer=args.by, disposition=getattr(args, "as"),
                                note=args.note or "")
    except Exception as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1
    print(f"recorded: {args.shard_id[:18]}… → {getattr(args, 'as')} by {args.by}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="axm", description="AXM Operator Console — your seat.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("surfaces", help="list capturable/operable surfaces").set_defaults(fn=cmd_surfaces)

    for verb in ("capture", "operate"):
        p = sub.add_parser(verb, help=f"{verb} a surface to a sealed, verified record")
        p.add_argument("surface")
        p.add_argument("-p", "--param", action="append", metavar="k=v")
        p.set_defaults(fn=_do_capture)

    pv = sub.add_parser("verify", help="verify any sealed shard, print its receipt")
    pv.add_argument("shard_dir")
    pv.add_argument("--key", required=True, help="out-of-band trusted public key")
    pv.set_defaults(fn=cmd_verify)

    pa = sub.add_parser("ask", help="verify-gated query of any sealed shard through Spectra")
    pa.add_argument("shard_dir")
    pa.add_argument("--key", default=None,
                    help="out-of-band trusted public key (required — the console never "
                         "queries an unverified shard)")
    pa.add_argument("--sql", default=None, help="raw SQL query, run in place of a free-text question")
    pa.set_defaults(fn=cmd_ask, question=None)
    # QUESTION is a free-text positional taken after --key/--sql: argparse's
    # positional matcher greedily starves a nargs='?' positional that sits
    # after a required one once an optional interrupts them (a long-standing
    # argparse limitation), so it is collected from parse_known_args()'s
    # leftovers in main() instead of declared as a second positional here.

    sub.add_parser("queue", help="show your review queue").set_defaults(fn=cmd_queue)

    pr = sub.add_parser("review", help="record a human review decision")
    pr.add_argument("shard_id")
    pr.add_argument("--by", required=True, metavar="NAME", help="human reviewer")
    pr.add_argument("--as", required=True, choices=["escalate", "dismiss", "needs_context"])
    pr.add_argument("--note", default="")
    pr.set_defaults(fn=cmd_review)

    return ap


def main(argv=None) -> int:
    parser = build_parser()
    args, extras = parser.parse_known_args(argv)
    if extras:
        if args.cmd == "ask":
            args.question = " ".join(extras)
        else:
            parser.error(f"unrecognized arguments: {' '.join(extras)}")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
