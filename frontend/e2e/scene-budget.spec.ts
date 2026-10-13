import {test,expect} from '@playwright/test';
import {PNG} from 'pngjs';
import {useLocalApi} from './local-api';

test('scene has non-blank pixels and stable resources across remounts',async({page},testInfo)=>{
  test.setTimeout(120000);
  const pages=testInfo.project.name==='pages';
  if(pages) await useLocalApi(page);
  await page.addInitScript(() => {
    const records: unknown[] = [];
    Object.assign(window, {sceneDisposals: records});
    window.addEventListener('urban:scene-disposed', event => records.push((event as CustomEvent).detail));
    const listeners=new Set<EventListenerOrEventListenerObject>();
    const add=document.addEventListener.bind(document), remove=document.removeEventListener.bind(document);
    document.addEventListener=((type:string,listener:EventListenerOrEventListenerObject,options?:boolean|AddEventListenerOptions)=>{
      if(type==='visibilitychange') listeners.add(listener);
      add(type,listener,options);
    }) as typeof document.addEventListener;
    document.removeEventListener=((type:string,listener:EventListenerOrEventListenerObject,options?:boolean|EventListenerOptions)=>{
      if(type==='visibilitychange') listeners.delete(listener);
      remove(type,listener,options);
    }) as typeof document.removeEventListener;
    Object.assign(window,{sceneListenerCount:()=>listeners.size});
  });
  await page.goto(pages?'/pathway-safety-urban-planning/#/signup':'/signup');
  await page.getByPlaceholder('Control Room Operator').fill('Scene budget operator');
  await page.getByPlaceholder('operator@urbanintel.in').fill(`budget_${Date.now()}@example.test`);
  await page.locator('input[type=password]').nth(0).fill('LocalSceneCheck123!');
  await page.locator('input[type=password]').nth(1).fill('LocalSceneCheck123!');
  await page.locator('button[type=submit]').click();
  await expect(page).toHaveURL(/app\/overview/);
  const baselineListeners=await page.evaluate(()=>(window as unknown as {sceneListenerCount:()=>number}).sceneListenerCount());
  await page.locator(`.app-sidebar a[href="${pages?'#':''}/app/digital-twin"]`).click();
  const metrics:{fps:number;geometries:number;textures:number;drawCalls:number}[]=[];
  for(let cycle=0;cycle<3;cycle++){
    const canvas=page.locator('.voxel-scene canvas');
    await expect(canvas).toBeVisible();
    await expect.poll(()=>canvas.getAttribute('data-fps'),{timeout:20000}).not.toBeNull();
    metrics.push(await canvas.evaluate(node=>{
      const d=(node as HTMLElement).dataset;
      return {fps:Number(d.fps),geometries:Number(d.geometries),textures:Number(d.textures),drawCalls:Number(d.drawCalls)};
    }));
    if(cycle===0){
      const screenshot=PNG.sync.read(await canvas.screenshot());
      const colors=new Set<number>();
      for(let i=0;i<screenshot.data.length;i+=64) colors.add(screenshot.data[i]*65536+screenshot.data[i+1]*256+screenshot.data[i+2]);
      expect(colors.size).toBeGreaterThan(100);
    }
    if(cycle<2){
      await page.getByRole('button',{name:'Geographic evidence',exact:true}).click();
      await expect(page.locator('.voxel-scene')).toHaveCount(0);
      expect(await page.evaluate(()=>(window as unknown as {sceneListenerCount:()=>number}).sceneListenerCount())).toBe(baselineListeners);
      await expect.poll(()=>page.evaluate(()=> (window as unknown as {sceneDisposals:unknown[]}).sceneDisposals.length),{timeout:10000}).toBeGreaterThan(cycle);
      await page.getByRole('button',{name:'Voxel metropolis',exact:true}).click();
    }
  }
  for(const entry of metrics){
    expect(entry.geometries).toBeGreaterThan(0);
    expect(entry.geometries).toBeLessThanOrEqual(metrics[0].geometries);
    expect(entry.textures).toBeLessThanOrEqual(metrics[0].textures);
  }
  console.log('SCENE_MEASUREMENT',JSON.stringify(metrics));
  const disposed = await page.evaluate(()=> (window as unknown as {sceneDisposals:{geometries:number;textures:number}[]}).sceneDisposals);
  console.log('SCENE_DISPOSED',JSON.stringify(disposed));
  expect(disposed.length).toBeGreaterThanOrEqual(2);
  for(const memory of disposed) {
    expect(memory.geometries).toBe(0);
    expect(memory.textures).toBe(0);
  }
  for(const width of [360,768,1280]){
    await page.setViewportSize({width,height:900});
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  }
});
