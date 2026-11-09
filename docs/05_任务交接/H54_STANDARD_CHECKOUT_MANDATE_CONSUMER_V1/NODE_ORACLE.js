// Frozen evaluator wrapper: positive JSON only. Invalid JSON/domain rejection is
// checked separately in Python; this JS reference is not an input validator.
'use strict';
const fs = require('fs');
const canonicalize = require('./sources/reference/canonicalize.js');
const obj = JSON.parse(fs.readFileSync(0, 'utf8'));
process.stdout.write(canonicalize(obj));
