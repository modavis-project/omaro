import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../../', import.meta.url));
const localPython = `${root}.venv/bin/python`;
const python = process.env.OMARO_PYTHON || (existsSync(localPython) ? localPython : 'python3');
const result = spawnSync(python, [fileURLToPath(new URL('./build.py', import.meta.url))], { stdio: 'inherit' });
if (result.error) console.error('Build could not start. Set OMARO_PYTHON to the installed OMARO Python interpreter.');
process.exit(result.status ?? 1);
