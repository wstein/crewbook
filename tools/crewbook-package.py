#!/usr/bin/env python3
"""Maintain the reviewed crewbook text artifact; no third-party packages needed."""
import argparse
import json
import os
import sys

import packagelint
from packagefmt import (MAX_INVENTORY, MAX_MANIFEST, PackageError, check,
                        check_layout, decode, digest, encode, export, load_policy,
                        object_fields, read_regular, runtime_check, scan,
                        write_inventory)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise PackageError(message)


def run(arguments, output=sys.stdout, diagnostics=sys.stderr):
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument('command', choices=('check', 'inventory', 'update', 'export', 'runtime-check', 'lock'))
    parser.add_argument('--root', required=True, help='canonical absolute package root')
    for name in ('policy', 'inventory', 'dest', 'pin', 'provider', 'source', 'commit'):
        parser.add_argument('--' + name)
    parser.add_argument('--identity', default='crewbook')
    parser.add_argument('--lint', action='store_true', help='with check: warn on preamble drift and duplicated rule text')
    args = parser.parse_args(arguments)
    if args.lint and args.command != 'check':
        raise PackageError('--lint applies only to check')
    policy_path = args.policy or os.path.join(args.root, 'tools/package-policy.json')
    inventory_path = args.inventory or os.path.join(args.root, 'tools/package.sha256')
    policy = load_policy(policy_path)
    snapshot = scan(args.root, policy)
    encoded = encode(snapshot.files)
    if args.command == 'inventory':
        output.write(encoded.decode('ascii'))
    elif args.command == 'update':
        check_layout(snapshot)
        write_inventory(args.root, inventory_path, policy_path, policy, encoded)
    elif args.command in ('check', 'export'):
        check(snapshot, read_regular(inventory_path, MAX_INVENTORY))
        check_layout(snapshot)
        if args.command == 'export':
            if not args.dest:
                raise PackageError('export requires --dest')
            export(snapshot, args.dest)
        else:
            diagnostics.write('source layout and inventory valid; runtime compatibility not established\n')
            if args.lint:
                found = packagelint.lint(snapshot.content)
                for line in found:
                    diagnostics.write('lint: ' + line + '\n')
                diagnostics.write('lint: %d warning(s); exit status unchanged\n' % len(found))
    else:
        if not snapshot.manifest:
            runtime_check(snapshot, {}, [], [])
        if not args.provider:
            raise PackageError('--provider requires independently trusted support and confirmed project inputs')
        support = object_fields(decode(read_regular(args.provider, MAX_MANIFEST)), ('bindings', 'project_inputs'))
        if args.command == 'lock':
            pin = {'identity': args.identity, 'source': args.source or '', 'commit': args.commit or '',
                   'manifest_sha256': digest(snapshot.manifest), 'inventory_sha256': digest(encoded),
                   'contract_version': 1}
        else:
            if not args.pin:
                raise PackageError('runtime-check requires --pin from an external reviewed operator lock')
            pin = decode(read_regular(args.pin, MAX_MANIFEST))
        runtime_check(snapshot, pin, support['bindings'], support['project_inputs'])
        if args.command == 'lock':
            output.write(json.dumps(pin, indent=2) + '\n')
        else:
            diagnostics.write('package matches external pin and supplied provider assertions; live client loading is not measured by this command\n')


def main():
    try:
        run(sys.argv[1:])
    except (PackageError, OSError, RecursionError) as error:
        print('crewbook-package: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
