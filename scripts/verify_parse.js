#!/usr/bin/env node
// ============================================================
// scripts/verify_parse.js
// Verifies the HTML dashboard's parseWorkbook + trailing-window
// math reproduces the workbook's own Metrics_Period results.
// Replicates the exact logic in VBX_Command_Center_Dashboard.html
// (readSheet, excelDateToJS, trailingCount, trailingSum) and
// cross-checks against the formula-computed engine.
//
// Usage: node scripts/verify_parse.js [path/to/workbook.xlsx]
// Exits non-zero on any mismatch.
// ============================================================
const XLSX = require('xlsx');

const WB_PATH = process.argv[2] || 'output/VBX_Command_Center_v1.xlsx';
const wb = XLSX.readFile(WB_PATH, { cellDates: true });

// ---- mirror of the HTML helpers --------------------------------
function excelDateToJS(v) {
  if (v instanceof Date) return v;
  if (typeof v === 'number') {
    // SheetJS epoch conversion (1899-12-30)
    return new Date(Math.round((v - 25569) * 86400 * 1000));
  }
  const d = new Date(v);
  return isNaN(d.getTime()) ? null : d;
}

function readSheet(sheetName, headerRow, columnMap) {
  if (!wb.SheetNames.includes(sheetName)) return [];
  const ws = wb.Sheets[sheetName];
  const range = XLSX.utils.decode_range(ws['!ref']);
  const rows = [];
  for (let R = headerRow; R <= range.e.r; R++) {
    const row = {};
    let hasData = false;
    for (const [field, col] of Object.entries(columnMap)) {
      const cell = ws[XLSX.utils.encode_cell({ r: R, c: col })];
      if (cell !== undefined && cell.v !== undefined && cell.v !== '') {
        row[field] = cell.v; hasData = true;
      } else { row[field] = null; }
    }
    if (hasData && row[Object.keys(columnMap)[0]] !== null) rows.push(row);
  }
  return rows;
}

function getCell(sheetName, ref) {
  if (!wb.SheetNames.includes(sheetName)) return null;
  const c = wb.Sheets[sheetName][ref];
  return c ? c.v : null;
}

const dayMs = 24 * 60 * 60 * 1000;
function daysAdd(d, n) { return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }

let AS_OF;
function trailingCount(rows, dateField, daysBack, offset = 0) {
  const hi = daysAdd(AS_OF, -offset);
  const lo = daysAdd(AS_OF, -(daysBack + offset));
  let count = 0;
  for (const r of rows) {
    const d = r[dateField];
    if (!d || !(d instanceof Date) || isNaN(d.getTime())) continue;
    if (offset === 0 ? (d >= lo && d <= hi) : (d >= lo && d < hi)) count++;
  }
  return count;
}
function trailingSum(rows, sumField, dateField, daysBack, offset = 0) {
  const hi = daysAdd(AS_OF, -offset);
  const lo = daysAdd(AS_OF, -(daysBack + offset));
  let sum = 0;
  for (const r of rows) {
    const d = r[dateField];
    if (!d || !(d instanceof Date) || isNaN(d.getTime())) continue;
    if (offset === 0 ? (d >= lo && d <= hi) : (d >= lo && d < hi)) sum += (r[sumField] || 0);
  }
  return sum;
}

// ---- parse, matching parseWorkbook column maps -----------------
AS_OF = excelDateToJS(getCell('Dashboard', 'C4'));

const screenings = readSheet('Screenings', 4, { num:0, company:1, contact:2, setAside:3, date:4, ndaDate:5, vertical:6, classification:7 })
  .map(r => ({ ...r, date: excelDateToJS(r.date) })).filter(r => r.date && r.company);
const ndas = readSheet('NDAs', 4, { num:0, entity:1, contact:2, date:3, filename:4, status:5, classification:6 })
  .map(r => ({ ...r, date: excelDateToJS(r.date) })).filter(r => r.date && r.entity);
const agreements = readSheet('Agreements', 4, { num:0, party:1, contact:2, date:3, type:4, filename:5, status:6, notes:7 })
  .map(r => ({ ...r, date: excelDateToJS(r.date) })).filter(r => r.date && r.party);
const meetings = readSheet('Meetings', 4, { date:0, partner:1, attendees:2, type:3, outcome:4, nextStep:5, owner:6 })
  .map(r => ({ ...r, date: excelDateToJS(r.date) })).filter(r => r.date);
const pipeline = readSheet('Pipeline', 4, { id:0, name:1, client:2, naics:3, stage:4, value:5, identified:6, stageDate:7, owner:8, notes:9 })
  .map(r => ({ ...r, identified: r.identified ? excelDateToJS(r.identified) : null })).filter(r => r.id);
const revenue = readSheet('Revenue_Ledger', 4, { date:0, client:1, contract:2, invoice:3, amount:4, paid:5, paidDate:6, notes:7 })
  .map(r => ({ ...r, date: excelDateToJS(r.date) })).filter(r => r.date);

// ---- checks vs Metrics_Period (formula-computed) ---------------
// Metrics_Period columns: C=T-7d(2), F=T-30d(5), K=T-91d(10)
const checks = [
  ['Screenings T-7d',  trailingCount(screenings, 'date', 7),  getCell('Metrics_Period', 'C5')],
  ['Screenings T-30d', trailingCount(screenings, 'date', 30), getCell('Metrics_Period', 'F5')],
  ['NDAs T-7d',        trailingCount(ndas, 'date', 7),        getCell('Metrics_Period', 'C6')],
  ['NDAs T-30d',       trailingCount(ndas, 'date', 30),       getCell('Metrics_Period', 'F6')],
  ['Agreements T-30d', trailingCount(agreements, 'date', 30), getCell('Metrics_Period', 'F7')],
  ['Meetings T-7d',    trailingCount(meetings, 'date', 7),    getCell('Metrics_Period', 'C8')],
  ['Meetings T-30d',   trailingCount(meetings, 'date', 30),   getCell('Metrics_Period', 'F8')],
  ['New Pipeline Opps T-30d', trailingCount(pipeline, 'identified', 30), getCell('Metrics_Period', 'F9')],
  ['Revenue $ T-7d',   trailingSum(revenue, 'amount', 'date', 7),  getCell('Metrics_Period', 'C13')],
  ['Revenue $ T-30d',  trailingSum(revenue, 'amount', 'date', 30), getCell('Metrics_Period', 'F13')],
  ['Revenue $ T-91d',  trailingSum(revenue, 'amount', 'date', 91), getCell('Metrics_Period', 'K13')],
];

let failures = 0;
console.log(`As_Of_Date = ${AS_OF.toISOString().slice(0,10)}   workbook = ${WB_PATH}\n`);
for (const [label, js, xl] of checks) {
  const ok = Math.abs((js || 0) - (xl || 0)) < 1e-6;
  if (!ok) failures++;
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${label.padEnd(26)} HTML=${String(js).padStart(8)}  workbook=${String(xl).padStart(8)}`);
}
console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED' : failures + ' MISMATCH(ES)'}  (${checks.length} metrics)`);
process.exit(failures === 0 ? 0 : 1);
