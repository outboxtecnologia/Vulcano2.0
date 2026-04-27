
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const container = document.getElementById('scene');

// ---------- renderer ----------
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0x090A0D, 1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
container.appendChild(renderer.domElement);

// ---------- scene + camera ----------
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x090A0D, 0.05);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 200);
camera.position.set(0, 9, 16);
camera.lookAt(0, 0, 0);

// ---------- lights ----------
scene.add(new THREE.AmbientLight(0x0B0F18, 0.55));
const keyLight = new THREE.DirectionalLight(0x8a9bb5, 0.65);
keyLight.position.set(-6, 14, 6);
scene.add(keyLight);
const rimLight = new THREE.DirectionalLight(0x2A4E73, 0.55);
rimLight.position.set(8, 4, -6);
scene.add(rimLight);
// lava glows from beneath — only visible through cracks
const fillLight = new THREE.PointLight(0xFF4500, 3.5, 24, 2);
fillLight.position.set(0, -0.6, 0);
scene.add(fillLight);

// ---------- hex tiles ----------
// Hex grid (pointy-top)
const HEX_R = 1.0;
const ROWS = 14;
const COLS = 18;

// Build a single tile geometry: hexagonal prism with bevel-ish via small extrusion
function makeHexGeom(radius = 1, height = 0.55) {
  const shape = new THREE.Shape();
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 3) * i + Math.PI / 6; // pointy-top
    const x = Math.cos(a) * radius;
    const y = Math.sin(a) * radius;
    if (i === 0) shape.moveTo(x, y); else shape.lineTo(x, y);
  }
  shape.closePath();
  const geom = new THREE.ExtrudeGeometry(shape, {
    depth: height, bevelEnabled: true,
    bevelThickness: 0.06, bevelSize: 0.06, bevelOffset: 0, bevelSegments: 2,
    curveSegments: 1
  });
  geom.rotateX(-Math.PI / 2); // lay flat
  geom.translate(0, height, 0);
  return geom;
}

const baseGeom = makeHexGeom(HEX_R * 0.97, 0.55);

// Custom shader material: dark basalt + glowing crack edges
const tileUniforms = {
  uTime:    { value: 0 },
  uHover:   { value: new THREE.Vector2(-999, -999) },
  uHoverR:  { value: 5.0 },
  uPulse:   { value: 0.0 },
  uClick:   { value: new THREE.Vector2(-999, -999) },
  uClickT:  { value: -10 },
};

const tileMat = new THREE.ShaderMaterial({
  uniforms: tileUniforms,
  vertexShader: /*glsl*/`
    varying vec3 vWorldPos;
    varying vec3 vLocalPos;
    varying vec3 vNormal;
    varying vec2 vBary;        // approx: dist from center within tile
    attribute vec3 instColor;
    attribute float instSeed;
    attribute float instH;     // per-instance height bias
    varying vec3 vInstColor;
    varying float vInstSeed;

    uniform float uTime;
    uniform vec2  uHover;
    uniform float uHoverR;
    uniform vec2  uClick;
    uniform float uClickT;
    varying float vMagmaRise;     // 0..1 how much magma is exposed near this tile

    void main() {
      vInstColor = instColor;
      vInstSeed  = instSeed;

      vec4 inst = instanceMatrix * vec4(position, 1.0);
      // tile world center (column 3 of instanceMatrix)
      vec3 tileCenter = vec3(instanceMatrix[3].x, instanceMatrix[3].y, instanceMatrix[3].z);

      // hover SINKS the tiles in a soft well so magma in the cracks rises above
      float dHover = distance(uHover, tileCenter.xz);
      float wellMask = smoothstep(uHoverR, 0.0, dHover);
      float sinkHover = -wellMask * 0.45;

      // click ripple — outward shockwave that sinks plates briefly so magma bursts up
      float age = max(0.0, uTime - uClickT);
      float ringR = age * 6.5;
      float dClick = distance(uClick, tileCenter.xz);
      float ringWidth = 1.6;
      float ring = exp(-pow((dClick - ringR)/ringWidth, 2.0)) * exp(-age*0.7);
      float sinkRipple = -ring * 1.0;

      // gentle breathing
      float breathe = sin(uTime*0.6 + instSeed*9.5)*0.06;

      vMagmaRise = clamp(wellMask + ring*0.9, 0.0, 1.0);

      vec3 lifted = inst.xyz;
      lifted.y += sinkHover + sinkRipple + breathe + instH;

      vec4 mv = modelViewMatrix * vec4(lifted, 1.0);
      vWorldPos = lifted;
      vLocalPos = position;
      vNormal   = normalize(normalMatrix * normal);
      vBary     = position.xz; // approx local xz (we rotated geom)
      gl_Position = projectionMatrix * mv;
    }
  `,
  fragmentShader: /*glsl*/`
    precision highp float;
    varying vec3 vWorldPos;
    varying vec3 vLocalPos;
    varying vec3 vNormal;
    varying vec2 vBary;
    varying vec3 vInstColor;
    varying float vInstSeed;
    varying float vMagmaRise;
    uniform float uTime;
    uniform vec2  uHover;
    uniform float uHoverR;

    float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }
    float noise(vec2 p){
      vec2 i=floor(p), f=fract(p);
      vec2 u=f*f*(3.0-2.0*f);
      return mix(mix(hash(i),hash(i+vec2(1,0)),u.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x), u.y);
    }
    float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<4;i++){v+=a*noise(p);p*=2.02;a*=0.5;} return v; }

    void main(){
      // top vs side: use world normal y
      float topness = clamp(vNormal.y, 0.0, 1.0);

      // distance to hex edge (approx, using local xz radius)
      float r = length(vBary);
      float rim = smoothstep(0.78, 0.97, r);

      // cold volcanic stone — obsidian / basalt / cobalt-steel palette
      vec2 wp = vWorldPos.xz * 0.6 + vInstSeed*30.0;
      float strat = fbm(wp*3.0);
      float micro = noise(wp*22.0)*0.5 + noise(wp*60.0)*0.25;
      // palette: #090A0D obsidian -> #1A1A1C basalt -> #2E3133 graphite -> #1E3A5F cobalt -> #2A4E73 steel -> #6D7078 mineral
      vec3 obsidian = vec3(0.035, 0.039, 0.051);   // #090A0D
      vec3 basalt   = vec3(0.102, 0.102, 0.110);   // #1A1A1C
      vec3 graphite = vec3(0.180, 0.192, 0.200);   // #2E3133
      vec3 cobalt   = vec3(0.118, 0.227, 0.373);   // #1E3A5F
      vec3 steel    = vec3(0.165, 0.306, 0.451);   // #2A4E73
      vec3 mineral  = vec3(0.427, 0.439, 0.471);   // #6D7078

      // base layer: obsidian -> basalt by strata
      vec3 rock = mix(obsidian, basalt, strat*0.7 + 0.2);
      // some tiles lean cobalt/steel (per-instance bias)
      float coolBias = step(0.55, vInstSeed);
      rock = mix(rock, mix(rock, cobalt, 0.55), coolBias * (0.3 + 0.5*strat));
      // micro highlights in graphite/mineral on top faces
      rock = mix(rock, graphite, micro*topness*0.45);
      rock = mix(rock, mineral, pow(topness, 3.0)*micro*0.35);
      // steel rim catch on bevel edges
      rock = mix(rock, steel, rim*topness*0.18);
      rock *= (0.55 + 0.55*topness);
      // heating from beneath when sinking — only this brings warmth
      rock += vec3(0.32, 0.10, 0.02) * vMagmaRise * topness * 0.30;

      // hairline cracks on top — very subtle, mostly cold
      float veins = fbm(wp*5.5);
      float veinMask = smoothstep(0.68, 0.88, veins) * topness;
      // veins only glow when magma is rising — orange-red palette
      vec3  veinCol  = vec3(1.000, 0.270, 0.000) * veinMask * vMagmaRise * 0.85;

      // edge lava — only at extreme rim, dim by default; intensifies when sinking
      float pulse = 0.55 + 0.45*sin(uTime*1.6 + vInstSeed*12.0);
      float flow  = fbm(vec2(r*30.0 + uTime*0.8, vInstSeed*20.0));
      float edgeMix = mix(flow, pulse, 0.5);
      float baseHeat = 0.18 + 0.82*vMagmaRise;

      vec3 col = rock;
      // palette: #FFB000 core -> #FF4500 mid -> #8B0000 ambient
      vec3 lavaCore = mix(vec3(1.000, 0.690, 0.000), vec3(1.000, 0.270, 0.000), 0.5+0.5*sin(uTime*0.8 + vInstSeed*20.0));
      vec3 lavaMid  = vec3(1.000, 0.270, 0.000);   // #FF4500
      vec3 lavaAmb  = vec3(0.545, 0.000, 0.000);   // #8B0000
      col += lavaAmb  * rim * topness * 0.35 * baseHeat;
      col += lavaMid  * smoothstep(0.88, 0.97, r) * topness * (0.4 + 0.5*edgeMix) * baseHeat;
      col += lavaCore * smoothstep(0.94, 0.99, r) * topness * (0.6 + 0.5*pulse) * baseHeat;

      // side glow only when magma rises (light leaking up between sunken plates)
      float sideGlow = (1.0 - topness) * smoothstep(0.0, 0.28, vWorldPos.y) * smoothstep(0.7, 0.0, vWorldPos.y - 0.45);
      col += lavaMid * sideGlow * 0.7 * vMagmaRise;

      col += veinCol;

      col = pow(col, vec3(0.92));
      gl_FragColor = vec4(col, 1.0);
    }
  `
});

// Build instanced mesh
const total = ROWS * COLS;
const inst = new THREE.InstancedMesh(baseGeom, tileMat, total);
inst.frustumCulled = false;

const colorAttr = new Float32Array(total * 3);
const seedAttr  = new Float32Array(total);
const heightAttr= new Float32Array(total);

const dummy = new THREE.Object3D();
const tmpColor = new THREE.Color();

const HX = HEX_R * Math.sqrt(3);   // horizontal spacing (pointy-top)
const HY = HEX_R * 1.5;            // row spacing

let idx = 0;
for (let r = 0; r < ROWS; r++) {
  for (let c = 0; c < COLS; c++) {
    const x = (c - COLS/2) * HX + ((r % 2) ? HX*0.5 : 0);
    const z = (r - ROWS/2) * HY;

    // organic variation
    const jx = (Math.random()-0.5)*0.06;
    const jz = (Math.random()-0.5)*0.06;
    const tilt = (Math.random()-0.5)*0.05;

    // height bias — most low, some risen
    const h = (Math.random() < 0.18 ? Math.random()*0.45 : 0) + (Math.random()-0.5)*0.06;
    heightAttr[idx] = h;

    dummy.position.set(x+jx, 0, z+jz);
    dummy.rotation.set(tilt, (Math.random()-0.5)*0.04, tilt);
    dummy.scale.setScalar(0.99);
    dummy.updateMatrix();
    inst.setMatrixAt(idx, dummy.matrix);

    // color tint per tile — cold stone, mostly obsidian/basalt with occasional cobalt
    const coolPick = Math.random();
    if (coolPick > 0.7) {
      // cobalt/steel-leaning tile
      tmpColor.setHSL(0.58 + Math.random()*0.04, 0.30, 0.10 + Math.random()*0.04);
    } else {
      // obsidian/basalt/graphite
      tmpColor.setHSL(0.60 + Math.random()*0.05, 0.04 + Math.random()*0.04, 0.05 + Math.random()*0.04);
    }
    colorAttr[idx*3+0] = tmpColor.r;
    colorAttr[idx*3+1] = tmpColor.g;
    colorAttr[idx*3+2] = tmpColor.b;

    seedAttr[idx] = Math.random();
    idx++;
  }
}
inst.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
inst.geometry.setAttribute('instColor', new THREE.InstancedBufferAttribute(colorAttr, 3));
inst.geometry.setAttribute('instSeed',  new THREE.InstancedBufferAttribute(seedAttr, 1));
inst.geometry.setAttribute('instH',     new THREE.InstancedBufferAttribute(heightAttr, 1));
scene.add(inst);

// ---------- floor lava plane (deep glow under cracks) ----------
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(80, 80),
  new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
    fragmentShader: `
      precision highp float; varying vec2 vUv; uniform float uTime;
      float hash(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
      float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f);
        return mix(mix(hash(i),hash(i+vec2(1,0)),u.x), mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x), u.y); }
      float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<4;i++){v+=a*noise(p);p*=2.02;a*=0.5;} return v; }
      void main(){
        vec2 p = (vUv-0.5)*8.0;
        float n = fbm(p + vec2(uTime*0.15, uTime*0.1));
        float n2= fbm(p*1.8 - vec2(uTime*0.05));
        // palette: #8B0000 -> #FF4500 -> #FFB000
        vec3 deep = vec3(0.545, 0.000, 0.000);
        vec3 mid  = vec3(1.000, 0.270, 0.000);
        vec3 hot  = vec3(1.000, 0.690, 0.000);
        vec3 col = mix(deep, mid, n2);
        col = mix(col, hot, smoothstep(0.55, 0.85, n));
        col *= (0.4 + 0.55*n);
        gl_FragColor = vec4(col, 1.0);
      }`
  })
);
floor.rotation.x = -Math.PI/2;
floor.position.y = -0.35;
scene.add(floor);

// ---------- post-processing ----------
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.85, 0.7, 0.32);
composer.addPass(bloom);

// chromatic aberration + subtle vignette pass
const chroma = new ShaderPass({
  uniforms: { tDiffuse: { value: null }, uTime: { value: 0 }, uAmount: { value: 0.0014 } },
  vertexShader: `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float uAmount; uniform float uTime; varying vec2 vUv;
    void main(){
      vec2 d = vUv - 0.5;
      float r = texture2D(tDiffuse, vUv + d*uAmount).r;
      float g = texture2D(tDiffuse, vUv).g;
      float b = texture2D(tDiffuse, vUv - d*uAmount).b;
      vec3 col = vec3(r,g,b);
      // vignette
      float v = smoothstep(1.2, 0.4, length(d*vec2(1.0,1.4)));
      col *= mix(0.55, 1.0, v);
      gl_FragColor = vec4(col, 1.0);
    }`
});
composer.addPass(chroma);
composer.addPass(new OutputPass());

// ---------- interaction ----------
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const groundPlane = new THREE.Plane(new THREE.Vector3(0,1,0), 0);
const hoverWorld = new THREE.Vector3();
const targetCam = { x: 0, y: 9, rx: 0, ry: 0 };

function onMove(e){
  const x = (e.clientX / window.innerWidth) * 2 - 1;
  const y = -(e.clientY / window.innerHeight) * 2 + 1;
  pointer.set(x, y);
  raycaster.setFromCamera(pointer, camera);
  raycaster.ray.intersectPlane(groundPlane, hoverWorld);
  tileUniforms.uHover.value.set(hoverWorld.x, hoverWorld.z);

  // camera parallax
  targetCam.ry = x * 0.18;
  targetCam.rx = -y * 0.10;
}
function onClick(e){
  const x = (e.clientX / window.innerWidth) * 2 - 1;
  const y = -(e.clientY / window.innerHeight) * 2 + 1;
  pointer.set(x, y);
  raycaster.setFromCamera(pointer, camera);
  const hit = new THREE.Vector3();
  raycaster.ray.intersectPlane(groundPlane, hit);
  tileUniforms.uClick.value.set(hit.x, hit.z);
  tileUniforms.uClickT.value = clock.getElapsedTime();
}
window.addEventListener('mousemove', onMove);
window.addEventListener('click', onClick);

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});

// ---------- loader curtain ----------
const curtain = document.getElementById('curtain');
const lbar = document.getElementById('lbar');
let loaded = 0;
const fakeLoad = setInterval(() => {
  loaded += 4 + Math.random()*8;
  if (loaded >= 100) { loaded = 100; clearInterval(fakeLoad); setTimeout(()=>curtain.classList.add('hidden'), 350); }
  lbar.style.width = loaded + '%';
}, 60);

// ---------- loop ----------
const clock = new THREE.Clock();
function animate(){
  const t = clock.getElapsedTime();
  tileUniforms.uTime.value = t;
  floor.material.uniforms.uTime.value = t;
  chroma.uniforms.uTime.value = t;

  // smooth camera
  camera.position.x += (targetCam.ry*4 - camera.position.x) * 0.04;
  camera.position.y += (9 + targetCam.rx*2 - camera.position.y) * 0.04;
  camera.lookAt(0, 0, 0);

  composer.render();
  requestAnimationFrame(animate);
}
animate();

// ---------- form interactions ----------
document.querySelectorAll('.input-wrap').forEach(w => {
  const input = w.querySelector('input');
  input.addEventListener('focus', () => w.classList.add('focus'));
  input.addEventListener('blur',  () => w.classList.remove('focus'));
});
const passInput = document.getElementById('passInput');
document.getElementById('togglePass').addEventListener('click', () => {
  passInput.type = passInput.type === 'password' ? 'text' : 'password';
});
document.getElementById('loginForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = e.target.querySelector('.btn-primary');
  btn.innerHTML = '<span>AUTENTICANDO...</span>';
  btn.disabled = true;
  setTimeout(() => { window.location.href = 'index.html'; }, 900);
});

// card 3D tilt
const card = document.getElementById('loginCard');
const wrap = card.parentElement;
wrap.addEventListener('mousemove', (e) => {
  const r = wrap.getBoundingClientRect();
  const x = (e.clientX - r.left)/r.width - 0.5;
  const y = (e.clientY - r.top)/r.height - 0.5;
  card.style.transform = `rotateY(${x*5}deg) rotateX(${-y*5}deg)`;
});
wrap.addEventListener('mouseleave', () => { card.style.transform = 'rotateY(0) rotateX(0)'; });
