import assert from 'node:assert/strict';
import fs from 'node:fs';
const html=fs.readFileSync(new URL('./index.html',import.meta.url),'utf8');
const js=fs.readFileSync(new URL('./app.js',import.meta.url),'utf8');
for(const text of ['Finca La Libertad','Soledad Sánchez','VillaYolsa','Yoleyda Sánchez','Agente AgroNexo']) assert.ok((html+js).includes(text),`missing ${text}`);
assert.ok((html+js).toLowerCase().includes('datos de demostración'),'missing demo-data label');
for(const view of ['dashboard','production','secondary','inventory','calendar','finance','alerts','team']) assert.ok(html.includes(`data-view="${view}"`),`missing view ${view}`);
assert.ok(js.includes('registrar')&&js.includes('localStorage'),'agent actions and session persistence');
console.log('PASS: contenido, módulos, dos fincas, agente y persistencia presentes');
