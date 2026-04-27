import React, { useEffect, useState, useRef } from 'react';
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export default function LoginView({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPass, setShowPass] = useState(false);

  const sceneRef = useRef(null);

  useEffect(() => {
    if (!sceneRef.current) return;
    const container = sceneRef.current;
    
    // Clear previous if any
    container.innerHTML = '';

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x090A0D, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x090A0D, 0.05);

    const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 200);
    camera.position.set(0, 9, 16);
    camera.lookAt(0, 0, 0);

    scene.add(new THREE.AmbientLight(0x0B0F18, 0.55));
    const keyLight = new THREE.DirectionalLight(0x8a9bb5, 0.65);
    keyLight.position.set(-6, 14, 6);
    scene.add(keyLight);
    const rimLight = new THREE.DirectionalLight(0x2A4E73, 0.55);
    rimLight.position.set(8, 4, -6);
    scene.add(rimLight);
    const fillLight = new THREE.PointLight(0xFF4500, 3.5, 24, 2);
    fillLight.position.set(0, -0.6, 0);
    scene.add(fillLight);

    const HEX_R = 1.0;
    const ROWS = 14;
    const COLS = 18;

    function makeHexGeom(radius = 1, height = 0.55) {
      const shape = new THREE.Shape();
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 3) * i + Math.PI / 6;
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
      geom.rotateX(-Math.PI / 2);
      geom.translate(0, height, 0);
      return geom;
    }

    const baseGeom = makeHexGeom(HEX_R * 0.97, 0.55);

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
      vertexShader: `
        varying vec3 vWorldPos;
        varying vec3 vLocalPos;
        varying vec3 vNormal;
        varying vec2 vBary;
        attribute vec3 instColor;
        attribute float instSeed;
        attribute float instH;
        varying vec3 vInstColor;
        varying float vInstSeed;

        uniform float uTime;
        uniform vec2  uHover;
        uniform float uHoverR;
        uniform vec2  uClick;
        uniform float uClickT;
        varying float vMagmaRise;

        void main() {
          vInstColor = instColor;
          vInstSeed  = instSeed;

          vec4 inst = instanceMatrix * vec4(position, 1.0);
          vec3 tileCenter = vec3(instanceMatrix[3].x, instanceMatrix[3].y, instanceMatrix[3].z);

          float dHover = distance(uHover, tileCenter.xz);
          float wellMask = smoothstep(uHoverR, 0.0, dHover);
          float sinkHover = -wellMask * 0.45;

          float age = max(0.0, uTime - uClickT);
          float ringR = age * 6.5;
          float dClick = distance(uClick, tileCenter.xz);
          float ringWidth = 1.6;
          float ring = exp(-pow((dClick - ringR)/ringWidth, 2.0)) * exp(-age*0.7);
          float sinkRipple = -ring * 1.0;

          float breathe = sin(uTime*0.6 + instSeed*9.5)*0.06;

          vMagmaRise = clamp(wellMask + ring*0.9, 0.0, 1.0);

          vec3 lifted = inst.xyz;
          lifted.y += sinkHover + sinkRipple + breathe + instH;

          vec4 mv = modelViewMatrix * vec4(lifted, 1.0);
          vWorldPos = lifted;
          vLocalPos = position;
          vNormal   = normalize(normalMatrix * normal);
          vBary     = position.xz;
          gl_Position = projectionMatrix * mv;
        }
      `,
      fragmentShader: `
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
          float topness = clamp(vNormal.y, 0.0, 1.0);
          float r = length(vBary);
          float rim = smoothstep(0.78, 0.97, r);
          vec2 wp = vWorldPos.xz * 0.6 + vInstSeed*30.0;
          float strat = fbm(wp*3.0);
          float micro = noise(wp*22.0)*0.5 + noise(wp*60.0)*0.25;
          vec3 obsidian = vec3(0.035, 0.039, 0.051);
          vec3 basalt   = vec3(0.102, 0.102, 0.110);
          vec3 graphite = vec3(0.180, 0.192, 0.200);
          vec3 cobalt   = vec3(0.118, 0.227, 0.373);
          vec3 steel    = vec3(0.165, 0.306, 0.451);
          vec3 mineral  = vec3(0.427, 0.439, 0.471);

          vec3 rock = mix(obsidian, basalt, strat*0.7 + 0.2);
          float coolBias = step(0.55, vInstSeed);
          rock = mix(rock, mix(rock, cobalt, 0.55), coolBias * (0.3 + 0.5*strat));
          rock = mix(rock, graphite, micro*topness*0.45);
          rock = mix(rock, mineral, pow(topness, 3.0)*micro*0.35);
          rock = mix(rock, steel, rim*topness*0.18);
          rock *= (0.55 + 0.55*topness);
          rock += vec3(0.32, 0.10, 0.02) * vMagmaRise * topness * 0.30;

          float veins = fbm(wp*5.5);
          float veinMask = smoothstep(0.68, 0.88, veins) * topness;
          vec3  veinCol  = vec3(1.000, 0.270, 0.000) * veinMask * vMagmaRise * 0.85;

          float pulse = 0.55 + 0.45*sin(uTime*1.6 + vInstSeed*12.0);
          float flow  = fbm(vec2(r*30.0 + uTime*0.8, vInstSeed*20.0));
          float edgeMix = mix(flow, pulse, 0.5);
          float baseHeat = 0.18 + 0.82*vMagmaRise;

          vec3 col = rock;
          vec3 lavaCore = mix(vec3(1.000, 0.690, 0.000), vec3(1.000, 0.270, 0.000), 0.5+0.5*sin(uTime*0.8 + vInstSeed*20.0));
          vec3 lavaMid  = vec3(1.000, 0.270, 0.000);
          vec3 lavaAmb  = vec3(0.545, 0.000, 0.000);
          col += lavaAmb  * rim * topness * 0.35 * baseHeat;
          col += lavaMid  * smoothstep(0.88, 0.97, r) * topness * (0.4 + 0.5*edgeMix) * baseHeat;
          col += lavaCore * smoothstep(0.94, 0.99, r) * topness * (0.6 + 0.5*pulse) * baseHeat;

          float sideGlow = (1.0 - topness) * smoothstep(0.0, 0.28, vWorldPos.y) * smoothstep(0.7, 0.0, vWorldPos.y - 0.45);
          col += lavaMid * sideGlow * 0.7 * vMagmaRise;

          col += veinCol;

          col = pow(col, vec3(0.92));
          gl_FragColor = vec4(col, 1.0);
        }
      `
    });

    const total = ROWS * COLS;
    const inst = new THREE.InstancedMesh(baseGeom, tileMat, total);
    inst.frustumCulled = false;

    const colorAttr = new Float32Array(total * 3);
    const seedAttr  = new Float32Array(total);
    const heightAttr= new Float32Array(total);

    const dummy = new THREE.Object3D();
    const tmpColor = new THREE.Color();

    const HX = HEX_R * Math.sqrt(3);
    const HY = HEX_R * 1.5;

    let idx = 0;
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS; c++) {
        const x = (c - COLS/2) * HX + ((r % 2) ? HX*0.5 : 0);
        const z = (r - ROWS/2) * HY;

        const jx = (Math.random()-0.5)*0.06;
        const jz = (Math.random()-0.5)*0.06;
        const tilt = (Math.random()-0.5)*0.05;

        const h = (Math.random() < 0.18 ? Math.random()*0.45 : 0) + (Math.random()-0.5)*0.06;
        heightAttr[idx] = h;

        dummy.position.set(x+jx, 0, z+jz);
        dummy.rotation.set(tilt, (Math.random()-0.5)*0.04, tilt);
        dummy.scale.setScalar(0.99);
        dummy.updateMatrix();
        inst.setMatrixAt(idx, dummy.matrix);

        const coolPick = Math.random();
        if (coolPick > 0.7) {
          tmpColor.setHSL(0.58 + Math.random()*0.04, 0.30, 0.10 + Math.random()*0.04);
        } else {
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

    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));
    const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 0.85, 0.7, 0.32);
    composer.addPass(bloom);

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
          float v = smoothstep(1.2, 0.4, length(d*vec2(1.0,1.4)));
          col *= mix(0.55, 1.0, v);
          gl_FragColor = vec4(col, 1.0);
        }`
    });
    composer.addPass(chroma);
    composer.addPass(new OutputPass());

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const groundPlane = new THREE.Plane(new THREE.Vector3(0,1,0), 0);
    const hoverWorld = new THREE.Vector3();
    const targetCam = { x: 0, y: 9, rx: 0, ry: 0 };

    const onMove = (e) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = -(e.clientY / window.innerHeight) * 2 + 1;
      pointer.set(x, y);
      raycaster.setFromCamera(pointer, camera);
      raycaster.ray.intersectPlane(groundPlane, hoverWorld);
      tileUniforms.uHover.value.set(hoverWorld.x, hoverWorld.z);
      targetCam.ry = x * 0.18;
      targetCam.rx = -y * 0.10;
    };

    const onClick = (e) => {
      const x = (e.clientX / window.innerWidth) * 2 - 1;
      const y = -(e.clientY / window.innerHeight) * 2 + 1;
      pointer.set(x, y);
      raycaster.setFromCamera(pointer, camera);
      const hit = new THREE.Vector3();
      raycaster.ray.intersectPlane(groundPlane, hit);
      tileUniforms.uClick.value.set(hit.x, hit.z);
      tileUniforms.uClickT.value = clock.getElapsedTime();
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('click', onClick);

    const onResize = () => {
      camera.aspect = window.innerWidth/window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      composer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', onResize);

    const clock = new THREE.Clock();
    let animationId;
    function animate(){
      const t = clock.getElapsedTime();
      tileUniforms.uTime.value = t;
      floor.material.uniforms.uTime.value = t;
      chroma.uniforms.uTime.value = t;
      camera.position.x += (targetCam.ry*4 - camera.position.x) * 0.04;
      camera.position.y += (9 + targetCam.rx*2 - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);
      composer.render();
      animationId = requestAnimationFrame(animate);
    }
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('click', onClick);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      // Remove child
      if (container.firstChild) {
         container.removeChild(container.firstChild);
      }
    };
  }, []);

  useEffect(() => {
    // loader curtain removal
    const curtain = document.getElementById('curtain');
    const lbar = document.getElementById('lbar');
    let loaded = 0;
    const fakeLoad = setInterval(() => {
      loaded += 4 + Math.random()*8;
      if (loaded >= 100) { 
        loaded = 100; 
        clearInterval(fakeLoad); 
        setTimeout(() => { if (curtain) curtain.classList.add('hidden'); }, 350); 
      }
      if (lbar) lbar.style.width = loaded + '%';
    }, 60);
    return () => clearInterval(fakeLoad);
  }, []);

  const handleMouseMoveCard = (e) => {
    const card = document.getElementById('loginCard');
    const wrap = card.parentElement;
    const r = wrap.getBoundingClientRect();
    const x = (e.clientX - r.left)/r.width - 0.5;
    const y = (e.clientY - r.top)/r.height - 0.5;
    card.style.transform = `rotateY(${x*5}deg) rotateX(${-y*5}deg)`;
  };

  const handleMouseLeaveCard = () => {
    const card = document.getElementById('loginCard');
    card.style.transform = 'rotateY(0) rotateX(0)';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Erro na autenticação");
      }
      if (data.success && onLogin) {
        onLogin(data.user);
      }
    } catch(err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <style>{`
        /* Minimal css injection to avoid conflicting with existing app css */
        .login-wrapper { position: fixed; inset: 0; z-index: 99999; background: #050304; color: #f0e6d8; font-family: 'Inter', system-ui, sans-serif; overflow: hidden; }
        .login-wrapper * { box-sizing: border-box; margin: 0; padding: 0; }
        .login-wrapper #scene { position: absolute; inset: 0; z-index: 0; }
        .login-wrapper #scene canvas { display: block; width: 100% !important; height: 100% !important; }
        .login-wrapper .vignette { position: absolute; inset: 0; z-index: 2; background: radial-gradient(ellipse 60% 50% at 30% 35%, rgba(255,90,20,0.10), transparent 60%), radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(0,0,0,0.55) 95%); pointer-events: none; }
        .login-wrapper .grain { position: absolute; inset: 0; z-index: 3; pointer-events: none; opacity: 0.06; mix-blend-mode: overlay; background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"); }
        .login-wrapper .frame { position: relative; z-index: 10; width: 100%; height: 100vh; display: grid; grid-template-rows: 64px 1fr 48px; padding: 20px 28px; }
        .login-wrapper .top { display: flex; align-items: center; justify-content: space-between; padding: 0 4px; }
        .login-wrapper .brand { display: flex; align-items: center; gap: 12px; }
        .login-wrapper .brand-mark { width: 36px; height: 36px; border-radius: 8px; background: radial-gradient(circle at 30% 30%, rgba(255,200,120,0.55), transparent 60%), linear-gradient(135deg, #ff8a2a 0%, #c93a12 60%, #4a1206 100%); box-shadow: 0 0 22px rgba(255,122,26,0.45), inset 0 1px 0 rgba(255,220,180,0.3); }
        .login-wrapper .brand-text .b1 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 16px; }
        .login-wrapper .brand-text .b2 { font-family: 'JetBrains Mono', monospace; font-size: 9.5px; color: #ff7a1a; letter-spacing: 0.24em; margin-top: 4px; }
        .login-wrapper .top-meta { display: flex; gap: 18px; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: rgba(240,230,216,0.85); letter-spacing: 0.18em; }
        .login-wrapper .top-meta .live::before { content:''; display:inline-block; width:6px; height:6px; border-radius:50%; background:#3dd68c; box-shadow:0 0 8px #3dd68c; margin-right:6px; animation: livePulse 1.8s ease-in-out infinite; }
        @keyframes livePulse { 0%,100%{opacity:1;} 50%{opacity:.45;} }
        .login-wrapper .main { display: grid; grid-template-columns: 1fr 440px; gap: 60px; align-items: center; padding: 0 4px; }
        .login-wrapper .hero-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #ff7a1a; letter-spacing: 0.32em; margin-bottom: 24px; display:inline-flex; align-items:center; gap:12px; }
        .login-wrapper .hero-eyebrow::before { content:''; width: 38px; height: 1px; background: linear-gradient(90deg, transparent, #ff7a1a); }
        .login-wrapper .hero h1 { font-family: 'Space Grotesk', sans-serif; font-size: clamp(48px, 5.6vw, 84px); font-weight: 600; line-height: 0.96; letter-spacing: -0.025em; color: #f6ecdf; margin-bottom: 22px; }
        .login-wrapper .hero h1 .accent { background: linear-gradient(180deg, #ffd28a 0%, #ff8a2a 45%, #c93a12 100%); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; animation: glow 5s ease-in-out infinite; }
        @keyframes glow { 0%,100%{filter: drop-shadow(0 0 12px rgba(255,140,42,0.18));} 50%{filter: drop-shadow(0 0 32px rgba(255,140,42,0.5));} }
        .login-wrapper .hero p { font-size: 16.5px; color: rgba(240,230,216,0.82); max-width: 560px; line-height: 1.6; margin-bottom: 36px; text-shadow: 0 1px 12px rgba(0,0,0,0.6); }
        .login-wrapper .stats { display: grid; grid-template-columns: repeat(3, max-content); gap: 36px; border-top: 1px solid rgba(255,160,80,0.12); padding-top: 22px; max-width: 560px; }
        .login-wrapper .stat-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.22em; color: rgba(240,230,216,0.72); margin-bottom: 6px; }
        .login-wrapper .stat-value { font-family: 'Space Grotesk', sans-serif; font-size: 22px; font-weight: 600; font-variant-numeric: tabular-nums; }
        .login-wrapper .stat-value .unit { color: rgba(240,230,216,0.75); font-size: 14px; margin-left: 4px; }
        .login-wrapper .card-wrap { perspective: 1400px; }
        .login-wrapper .card { position: relative; background: linear-gradient(180deg, rgba(20,12,8,0.55) 0%, rgba(8,5,4,0.78) 100%); border: 1px solid rgba(255,160,80,0.18); border-radius: 14px; padding: 32px 32px 28px; backdrop-filter: blur(22px) saturate(140%); -webkit-backdrop-filter: blur(22px) saturate(140%); box-shadow: 0 40px 100px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,220,180,0.06); transition: transform 0.18s cubic-bezier(.2,.8,.2,1); transform-style: preserve-3d; }
        .login-wrapper .card::before { content:''; position: absolute; inset: -1px; border-radius: 14px; padding: 1px; background: linear-gradient(135deg, transparent 30%, rgba(255,140,42,0.45) 50%, transparent 70%); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; opacity: 0.7; pointer-events: none; }
        .login-wrapper .card-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.28em; color: #ff7a1a; margin-bottom: 10px; display:flex; align-items:center; gap:10px; }
        .login-wrapper .card-eyebrow .dot { width: 4px; height: 4px; border-radius: 50%; background: #ff7a1a; box-shadow: 0 0 8px #ff7a1a; }
        .login-wrapper .card h2 { font-family: 'Space Grotesk', sans-serif; font-size: 26px; font-weight: 600; letter-spacing: -0.015em; margin-bottom: 6px; }
        .login-wrapper .card-sub { font-size: 13px; color: rgba(240,230,216,0.78); margin-bottom: 26px; }
        .login-wrapper .field { margin-bottom: 14px; }
        .login-wrapper .field-label { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.2em; color: rgba(240,230,216,0.82); margin-bottom: 7px; }
        .login-wrapper .field-label a { color: rgba(255,176,0,0.95); text-decoration: none; font-size: 10px; letter-spacing: 0.16em; }
        .login-wrapper .field-label a:hover { color: #FFB000; }
        .login-wrapper .input-wrap { position: relative; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,160,80,0.14); border-radius: 8px; transition: all 160ms; }
        .login-wrapper .input-wrap:focus-within { border-color: rgba(255,140,42,0.6); background: rgba(0,0,0,0.55); box-shadow: 0 0 0 4px rgba(255,140,42,0.08), 0 0 24px rgba(255,140,42,0.14); }
        .login-wrapper .input-wrap input { width:100%; background:transparent; border:none; outline:none; color:#f0e6d8; font-family:'Inter',sans-serif; font-size:14px; padding:13px 44px 13px 16px; }
        .login-wrapper .input-wrap input::placeholder { color: rgba(240,230,216,0.45); }
        .login-wrapper .input-icon { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); color: rgba(240,230,216,0.6); cursor: pointer; }
        .login-wrapper .input-icon:hover { color: #FFB000; }
        .login-wrapper .options { display: flex; align-items: center; justify-content: space-between; margin: 4px 0 22px; }
        .login-wrapper .check { display: inline-flex; align-items: center; gap: 9px; cursor: pointer; font-size: 12.5px; color: rgba(240,230,216,0.85); }
        .login-wrapper .check input { display: none; }
        .login-wrapper .check .box { width: 16px; height: 16px; border: 1px solid rgba(255,160,80,0.25); border-radius: 4px; background: rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; }
        .login-wrapper .check input:checked + .box { background: linear-gradient(135deg, #ff8a2a, #c93a12); border-color: transparent; }
        .login-wrapper .check input:checked + .box::after { content:''; width: 8px; height: 4px; border-left: 2px solid #1a0a04; border-bottom: 2px solid #1a0a04; transform: rotate(-45deg) translate(1px,-1px); }
        .login-wrapper .btn-primary { width: 100%; padding: 14px 18px; border: none; border-radius: 8px; background: linear-gradient(135deg, #ff8a2a 0%, #c93a12 100%); color: #1a0a04; font-family: 'Inter', sans-serif; font-weight: 600; font-size: 14px; letter-spacing: 0.04em; cursor: pointer; position: relative; overflow: hidden; box-shadow: 0 8px 24px rgba(201,58,18,0.45), 0 0 36px rgba(255,140,42,0.3), inset 0 1px 0 rgba(255,220,180,0.4); transition: all 140ms; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .login-wrapper .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 12px 32px rgba(201,58,18,0.55), 0 0 48px rgba(255,140,42,0.4); }
        .login-wrapper .btn-primary::before { content:''; position:absolute; top:0; left:-50%; width:50%; height:100%; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent); transform: skewX(-20deg); transition: left 600ms; }
        .login-wrapper .btn-primary:hover::before { left: 150%; }
        .login-wrapper .divider { margin: 22px 0 16px; display: flex; align-items: center; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.22em; color: rgba(240,230,216,0.6); }
        .login-wrapper .divider::before, .login-wrapper .divider::after { content:''; flex:1; height:1px; background: linear-gradient(90deg, transparent, rgba(255,160,80,0.14), transparent); }
        .login-wrapper .sso { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
        .login-wrapper .sso button { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,160,80,0.18); color: rgba(240,230,216,0.95); padding: 11px 12px; border-radius: 7px; font-family:'Inter',sans-serif; font-size: 13px; cursor: pointer; transition: all 140ms; display:flex; align-items:center; justify-content:center; gap:8px; }
        .login-wrapper .sso button:hover { border-color: rgba(255,160,80,0.28); background: rgba(255,160,80,0.06); color: #f0e6d8; }
        .login-wrapper .sso button svg { width: 14px; height: 14px; }
        .login-wrapper .card-foot { margin-top: 18px; text-align: center; font-size: 12px; color: rgba(240,230,216,0.7); }
        .login-wrapper .card-foot a { color: rgba(255,176,0,0.95); text-decoration: none; }
        .login-wrapper .card-foot a:hover { color: #FFB000; }
        .login-wrapper .foot { display: flex; align-items: center; justify-content: space-between; padding: 0 4px; font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 0.2em; color: rgba(240,230,216,0.7); }
        .login-wrapper .foot .links { display: flex; gap: 22px; }
        .login-wrapper .foot a { color: inherit; text-decoration: none; }
        .login-wrapper .foot a:hover { color: #ff9a4a; }
        .login-wrapper .reveal { opacity: 0; transform: translateY(14px); animation: reveal 900ms cubic-bezier(.2,.8,.2,1) forwards; }
        .login-wrapper .reveal.d1 { animation-delay: 200ms; } .login-wrapper .reveal.d2 { animation-delay: 380ms; } .login-wrapper .reveal.d3 { animation-delay: 540ms; } .login-wrapper .reveal.d4 { animation-delay: 700ms; } .login-wrapper .reveal.d5 { animation-delay: 860ms; }
        @keyframes reveal { to { opacity: 1; transform: translateY(0); } }
        .login-wrapper .curtain { position: absolute; inset: 0; z-index: 99; background: #050304; display: flex; align-items: center; justify-content: center; transition: opacity 800ms ease; }
        .login-wrapper .curtain.hidden { opacity: 0; pointer-events: none; }
        .login-wrapper .curtain .l-text { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 0.4em; color: #ff7a1a; }
        .login-wrapper .curtain .l-bar { width: 220px; height: 1px; background: rgba(255,140,42,0.15); margin-top: 16px; overflow: hidden; }
        .login-wrapper .curtain .l-bar i { display: block; height: 100%; width: 0%; background: linear-gradient(90deg, #ff8a2a, #ffd28a); box-shadow: 0 0 16px #ff8a2a; transition: width 0.3s; }
        @media (max-width: 1100px) { .login-wrapper .main { grid-template-columns: 1fr; } .login-wrapper .hero h1 { font-size: 52px; } }
      `}
      </style>

      <div id="scene" ref={sceneRef}></div>
      <div className="vignette"></div>
      <div className="grain"></div>

      <div className="curtain" id="curtain">
        <div style={{ textAlign: "center" }}>
          <div className="l-text">FORJANDO O TERRENO</div>
          <div className="l-bar"><i id="lbar"></i></div>
        </div>
      </div>

      <div className="frame">
        <header className="top reveal">
          <div className="brand">
            <div className="brand-mark"></div>
            <div className="brand-text">
              <div className="b1">VULCANO</div>
              <div className="b2">CONTÁBIL · 2.0</div>
            </div>
          </div>
          <div className="top-meta">
            <span className="live">SISTEMAS · ONLINE</span>
            <span>v2.0.14</span>
            <span>SP · BR</span>
          </div>
        </header>

        <div className="main">
          <section className="hero">
            <div className="hero-eyebrow reveal d1">PLATAFORMA DE CONCILIAÇÃO E AUDITORIA</div>
            <h1 className="reveal d2">Onde o caos<br/>contábil <span className="accent">vira ordem</span>.</h1>
            <p className="reveal d3">Conciliação de ERPs, aplicação automática do CPC 47 e auditoria contínua — do contrato à última parcela.</p>
            <div className="stats reveal d4">
              <div><div className="stat-label">CONTAS ATIVAS</div><div className="stat-value">2.847</div></div>
              <div><div className="stat-label">VGV CONCILIADO</div><div className="stat-value">R$ 1,42<span className="unit">B</span></div></div>
              <div><div className="stat-label">UPTIME · 90D</div><div className="stat-value">99,98<span className="unit">%</span></div></div>
            </div>
          </section>

          <aside className="card-wrap reveal d3" onMouseMove={handleMouseMoveCard} onMouseLeave={handleMouseLeaveCard}>
            <div className="card" id="loginCard">
              <div className="card-eyebrow"><span className="dot"></span>ACESSO RESTRITO</div>
              <h2>Entrar no Vulcano</h2>
              <div className="card-sub">Use o e-mail corporativo da sua organização contábil.</div>
              {error && <div style={{ color: '#ff4a4a', fontSize: '13px', marginBottom: '12px', border: '1px solid #ff4a4a40', background: '#ff4a4a10', padding: '8px', borderRadius: '4px' }}>{error}</div>}
              <form id="loginForm" autoComplete="on" onSubmit={handleSubmit}>
                <div className="field">
                  <div className="field-label"><span>USUÁRIO / E-MAIL</span></div>
                  <div className="input-wrap" id="iw-user">
                    <input type="text" name="email" placeholder="voce@empresa.com.br" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" />
                    <span className="input-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M3 7l9 6 9-6M5 19h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2z"></path></svg></span>
                  </div>
                </div>
                <div className="field">
                  <div className="field-label"><span>SENHA</span><a href="#">RECUPERAR ACESSO →</a></div>
                  <div className="input-wrap" id="iw-pass">
                    <input type={showPass ? "text" : "password"} id="passInput" placeholder="••••••••••••" required value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" />
                    <span className="input-icon" id="togglePass" onClick={() => setShowPass(!showPass)} style={{cursor: 'pointer'}}><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"></path><circle cx="12" cy="12" r="3"></circle></svg></span>
                  </div>
                </div>
                <div className="options">
                  <label className="check"><input type="checkbox" defaultChecked /><span className="box"></span>Manter conectado por 30 dias</label>
                </div>
                <button className="btn-primary" type="submit" disabled={loading}>
                  <span>{loading ? 'AUTENTICANDO...' : 'ENTRAR'}</span>
                  {!loading && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>}
                </button>
                <div className="divider">OU</div>
                <div className="sso">
                  <button type="button"><svg viewBox="0 0 48 48"><path fill="#fbc02d" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.5-5.9 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 6.5 29.5 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.4-.4-3.5z"></path><path fill="#e53935" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.5 7 29.5 5 24 5 16.3 5 9.7 9 6.3 14.7z"></path><path fill="#4caf50" d="M24 43.5c5.3 0 10.2-2 14-5.4l-6.5-5.5c-2.1 1.5-4.7 2.4-7.5 2.4-5.4 0-9.6-3.4-11.3-8L6.4 32C9.7 38.5 16.3 43.5 24 43.5z"></path><path fill="#1565c0" d="M43.6 20.5H42V20H24v8h11.3c-.7 2-2.1 3.7-3.8 4.9l6.5 5.5C42.6 35.4 45.5 30.1 45.5 24c0-1.2-.1-2.4-.4-3.5z"></path></svg>SSO Google</button>
                  <button type="button"><svg viewBox="0 0 24 24" fill="#f0e6d8"><path d="M12 2C6.5 2 2 6.5 2 12c0 4.4 2.9 8.2 6.8 9.5.5.1.7-.2.7-.5v-1.7c-2.8.6-3.4-1.3-3.4-1.3-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.4 1.1 3 .8.1-.7.4-1.1.6-1.4-2.2-.3-4.6-1.1-4.6-5 0-1.1.4-2 1-2.7-.1-.3-.5-1.3.1-2.7 0 0 .8-.3 2.7 1 .8-.2 1.7-.3 2.5-.3.9 0 1.7.1 2.5.3 1.9-1.3 2.7-1 2.7-1 .5 1.4.2 2.4.1 2.7.6.7 1 1.6 1 2.7 0 3.9-2.4 4.7-4.6 5 .4.3.7.9.7 1.8v2.6c0 .3.2.6.7.5 4-1.3 6.8-5 6.8-9.5C22 6.5 17.5 2 12 2z"></path></svg>SAML / SSO</button>
                </div>
              </form>
              <div className="card-foot">Sem acesso? Solicite ao seu <a href="#">administrador</a> · <a href="#">Status</a></div>
            </div>
          </aside>
        </div>

        <footer className="foot reveal d5">
          <span>© 2026 VULCANO · LGPD · ISO 27001 · SOC 2 TYPE II</span>
          <div className="links"><a href="#">DOCS</a><a href="#">PRIVACIDADE</a><a href="#">CONTATO</a><a href="#">VOLTAR</a></div>
        </footer>
      </div>
    </div>
  );
}
