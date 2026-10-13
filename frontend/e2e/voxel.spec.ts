import { test, expect } from '@playwright/test';
import { createActors, signalPhase, stepActor } from '../src/features/three/voxelSimulation';
import { entities, parts } from '../src/features/three/voxelWorld';

test('voxel simulation preserves road, rail, signal and asset contracts',()=>{
 expect(parts.length).toBeGreaterThan(10000);
 for(const type of ['Railway station','Airport','Bus terminal','Office tower','Signal-controlled intersection'])expect(entities.some(e=>e.type===type)).toBeTruthy();
 expect([0,10,12,22,24,28].map(signalPhase)).toEqual(['EAST_WEST','AMBER_EW','NORTH_SOUTH','AMBER_NS','CROSSING','EAST_WEST']);
 const actors=createActors(false),car=actors.find(a=>a.lane===0)!;
 // Eastbound lane on z=-22 approaching the first stopline x=-74.
 car.distance=10;stepActor(car,1,13);expect(car.p[0]).toBeLessThanOrEqual(-74.09);const stop=car.p[0];stepActor(car,1,13);expect(car.p[0]).toBe(stop);stepActor(car,1,0);expect(car.p[0]).toBeGreaterThan(stop);
 for(const actor of actors.filter(a=>a.type==='Metro train'))for(let i=0;i<200;i++){stepActor(actor,.5,i*.5);expect(actor.p[1]).toBe(8.25);expect(Math.abs(actor.p[0])).toBeLessThanOrEqual(85);}
 const aircraft=actors.find(a=>a.type==='Aircraft')!;stepActor(aircraft,1,100);expect(aircraft.p).toEqual([-65,.3,-56]);stepActor(aircraft,1,170);expect(aircraft.p[1]).toBeGreaterThan(1);
});

test('immersive voxel world controls, geographic sync and mobile reduced motion',async({page})=>{
 test.setTimeout(90000);const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/signup');await page.getByPlaceholder('Control Room Operator').fill('Voxel QA');await page.getByPlaceholder('operator@urbanintel.in').fill(`voxel_${Date.now()}@example.com`);await page.locator('input[type=password]').nth(0).fill('LocalTestPassword123!');await page.locator('input[type=password]').nth(1).fill('LocalTestPassword123!');await page.locator('button[type=submit]').click();await expect(page).toHaveURL(/app\/overview/);
 await page.locator('.app-sidebar a[href="/app/digital-twin"]').click();await expect(page.locator('h1')).toContainText('Metropolis workspace');await expect(page.locator('.scene-loading')).toHaveCount(0);
 const scene=page.locator('.voxel-scene');await expect.poll(async()=>Number(await scene.getAttribute('data-sim-time'))).toBeGreaterThan(0);
 await page.getByLabel('Explore district').selectOption({label:'Grand Central terminus'});await expect(page.locator('.voxel-selection')).toContainText('Six platforms');await page.getByLabel('Focus selected entity').click();await page.getByLabel('Pause camera motion').click();await expect(scene).toHaveAttribute('data-paused','true');
 const frozen=await scene.getAttribute('data-sim-time');await page.getByLabel('Switch to day').click();await expect(scene).toContainText('DAY');await page.getByLabel('Switch to night').click();await page.getByLabel('Low detail mode').click();await expect(scene).toHaveAttribute('data-quality','low');expect(await scene.getAttribute('data-sim-time')).toBe(frozen);
 await scene.screenshot({path:'../../../outputs/voxel-station.png'});
 await page.getByLabel('Close entity details').click();await page.getByLabel('Reset camera').click();await page.getByLabel('Low detail mode').click();await scene.screenshot({path:'../../../outputs/voxel-workspace.png'});
 const canvas=page.locator('.voxel-scene canvas');const before=await canvas.screenshot();const box=await canvas.boundingBox();await page.mouse.move(box!.x+box!.width*.5,box!.y+box!.height*.6);await page.mouse.down();await page.mouse.move(box!.x+box!.width*.65,box!.y+box!.height*.65,{steps:12});await page.mouse.up();expect((await canvas.screenshot()).equals(before)).toBeFalsy();
 await page.getByLabel('Selected city',{exact:true}).selectOption('Chennai');await expect(scene).toContainText('CHENNAI CONTEXT');await page.getByRole('button',{name:'Geographic evidence',exact:true}).click();await expect(page.locator('.geo-caption')).toContainText('13.08270');await expect(page.locator('.map-canvas')).toHaveAttribute('data-center','13.08270,80.27070');
 await page.getByRole('button',{name:'Voxel metropolis',exact:true}).click();await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});await expect(scene).toHaveAttribute('data-paused','true');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:'../../../outputs/voxel-mobile.png',fullPage:false});expect(errors).toEqual([]);
});
