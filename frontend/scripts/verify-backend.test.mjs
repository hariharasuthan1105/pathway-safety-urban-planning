import test from 'node:test';
import assert from 'node:assert/strict';
import {validateBackendOrigin, verifyBackend} from './verify-backend.mjs';

for (const value of [undefined, '', ' ', 'not a url', 'https:example.test', 'https://', 'http://example.test', 'https://localhost', 'https://127.0.0.1', 'https://[::1]', 'https://user:password@example.test', 'https://example.test/api', 'https://example.test?x=1', 'https://example.test#fragment', 'https://example.test/']) {
  test(`invalid configuration is actionable: ${value?.includes('password') ? 'credentials' : value}`, async () => {
    let requested=false;
    await assert.rejects(verifyBackend(value,async()=>{requested=true;}),/Settings.*Actions.*Variables.*VITE_API_BASE_URL/);
    assert.equal(requested,false);
  });
}
test('normalizes whitespace',()=>{
  assert.equal(validateBackendOrigin(' https://example.test '),'https://example.test');
});
test('checks the configured health endpoint and accepts healthy JSON',async()=>{
  const origin=await verifyBackend('https://example.test',async(url,options)=>{
    assert.equal(url,'https://example.test/api/health');assert.ok(options.signal);
    return {ok:true,json:async()=>({status:'HEALTHY'})};
  });assert.equal(origin,'https://example.test');
});
test('HTTP failure blocks publication',async()=>{
  await assert.rejects(verifyBackend('https://example.test',async()=>({ok:false,status:503})),/HTTP 503/);
});
test('unhealthy JSON blocks publication',async()=>{
  await assert.rejects(verifyBackend('https://example.test',async()=>({ok:true,json:async()=>({status:'UNHEALTHY'})})),/did not report HEALTHY/);
});
test('invalid JSON blocks publication',async()=>{
  await assert.rejects(verifyBackend('https://example.test',async()=>({ok:true,json:async()=>{throw new Error('invalid');}})),/valid JSON/);
});
test('network failure blocks publication',async()=>{
  await assert.rejects(verifyBackend('https://example.test',async()=>{throw new Error('offline');}),/offline/);
});

test('retries cold starts, then requires healthy JSON', async () => {
  let calls=0, waits=0;
  await verifyBackend('https://example.test', async () => ++calls < 4 ? {ok:false,status:503} : {ok:true,status:200,json:async()=>({status:'HEALTHY'})}, {attempts:4,wait:async()=>{waits++;}});
  assert.equal(calls,4); assert.equal(waits,3);
});
test('exhausted retries still block publication', async () => {
  let calls=0;
  await assert.rejects(verifyBackend('https://example.test',async()=>{calls++;throw new Error('offline');},{attempts:4,wait:async()=>{}}), /after 4 attempt/);
  assert.equal(calls,4);
});
