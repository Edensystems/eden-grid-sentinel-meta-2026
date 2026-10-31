#!/usr/bin/env sh
set -eu
mkdir -p tests/contract-built
# Compile contract with no Next/React dependencies; test with Node built-ins.
tsc lib/contract.ts --target ES2022 --module nodenext --moduleResolution nodenext --skipLibCheck --outDir tests/contract-built
node --test tests/contract.test.mjs
