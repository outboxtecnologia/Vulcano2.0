import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export default function LavaBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x070506, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 0.95;
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06070A, 0.06);
    
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 200);
    camera.position.set(0, 11, 18);
    camera.lookAt(0, 0, 0);

    scene.add(new THREE.AmbientLight(0x0B0F18, 0.55));
    const k = new THREE.DirectionalLight(0x8a9bb5, 0.6);
    k.position.set(-6, 14, 6);
    scene.add(k);
    
    const rLight = new THREE.DirectionalLight(0x2A4E73, 0.5);
    rLight.position.set(8, 4, -6);
    scene.add(rLight);
    
    const fill = new THREE.PointLight(0xFF4500, 3.0, 24, 2);
    fill.position.set(0, -0.6, 0);
    scene.add(fill);

    const HEX_R = 1.0;
    const ROWS = 14;
    const COLS = 22;

    function makeHex(rad = 1, h = 0.55) {
      const s = new THREE.Shape();
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 3) * i + Math.PI / 6;
        const x = Math.cos(a) * rad;
        const y = Math.sin(a) * rad;
        if (i === 0) s.moveTo(x, y); else s.lineTo(x, y);
      }
      s.closePath();
      const g = new THREE.ExtrudeGeometry(s, {
        depth: h, bevelEnabled: true, bevelThickness: .06, bevelSize: .06, bevelOffset: 0, bevelSegments: 2, curveSegments: 1
      });
      g.rotateX(-Math.PI / 2);
      g.translate(0, h, 0);
      return g;
    }

    const baseGeom = makeHex(HEX_R * 0.97, 0.55);
    const u = {
      uTime: { value: 0 },
      uHover: { value: new THREE.Vector2(-999, -999) },
      uHoverR: { value: 5.0 },
      uScroll: { value: 0 }
    };

    const mat = new THREE.ShaderMaterial({
      uniforms: u,
      vertexShader: `
        attribute float instSeed; attribute float instH;
        varying float vMagma; varying vec3 vN; varying vec2 vXZ; varying float vSeed;
        uniform float uTime; uniform vec2 uHover; uniform float uHoverR; uniform float uScroll;
        void main(){
          vec4 inst = instanceMatrix * vec4(position, 1.0);
          vec3 c = vec3(instanceMatrix[3].x, instanceMatrix[3].y, instanceMatrix[3].z);
          float d = distance(uHover, c.xz);
          float well = smoothstep(uHoverR, 0.0, d);
          float breathe = sin(uTime * 0.6 + instSeed * 9.0) * 0.06;
          float scrollWobble = sin(uTime * 0.5 + c.x * 0.4 + uScroll * 0.005) * 0.10 * uScroll * 0.0008;
          vMagma = clamp(well, 0.0, 1.0);
          vec3 p = inst.xyz; p.y += -well * 0.45 + breathe + instH + scrollWobble;
          vN = normalize(normalMatrix * normal); vXZ = position.xz; vSeed = instSeed;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(p, 1.0);
        }`,
      fragmentShader: `
        precision highp float; varying float vMagma; varying vec3 vN; varying vec2 vXZ; varying float vSeed;
        uniform float uTime;
        float h(vec2 p){p=fract(p*vec2(123.34,456.21));p+=dot(p,p+45.32);return fract(p.x*p.y);}
        float n(vec2 p){vec2 i=floor(p),f=fract(p);vec2 u=f*f*(3.0-2.0*f);return mix(mix(h(i),h(i+vec2(1,0)),u.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),u.x),u.y);}
        float fbm(vec2 p){float v=0.0,a=0.5;for(int i=0;i<4;i++){v+=a*n(p);p*=2.02;a*=0.5;}return v;}
        void main(){
          float top = clamp(vN.y, 0.0, 1.0);
          float r = length(vXZ);
          float rim = smoothstep(0.78, 0.97, r);
          vec2 wp = vXZ * 0.6 + vSeed * 30.0;
          float strat = fbm(wp * 3.0);
          vec3 obs=vec3(.035,.039,.051), bas=vec3(.102,.102,.110), gra=vec3(.18,.192,.20), cob=vec3(.118,.227,.373), ste=vec3(.165,.306,.451), min_=vec3(.427,.439,.471);
          vec3 rock = mix(obs, bas, strat * 0.7 + 0.2);
          float cool = step(0.55, vSeed);
          rock = mix(rock, mix(rock, cob, 0.55), cool * (0.3 + 0.5 * strat));
          rock = mix(rock, gra, n(wp * 22.0) * top * 0.45);
          rock = mix(rock, min_, pow(top, 3.0) * 0.25);
          rock = mix(rock, ste, rim * top * 0.18);
          rock *= (0.55 + 0.55 * top);
          rock += vec3(0.32, 0.10, 0.02) * vMagma * top * 0.30;
          vec3 col = rock;
          vec3 lavaCore = vec3(1.0, 0.69, 0.0), lavaMid = vec3(1.0, 0.27, 0.0), lavaAmb = vec3(.545, 0.0, 0.0);
          float pulse = 0.55 + 0.45 * sin(uTime * 1.6 + vSeed * 12.0);
          float base = 0.18 + 0.82 * vMagma;
          col += lavaAmb * rim * top * 0.35 * base;
          col += lavaMid * smoothstep(0.88, 0.97, r) * top * (0.4 + 0.5 * pulse) * base;
          col += lavaCore * smoothstep(0.94, 0.99, r) * top * (0.6 + 0.5 * pulse) * base;
          col = pow(col, vec3(0.92));
          gl_FragColor = vec4(col, 1.0);
        }`
    });

    const total = ROWS * COLS;
    const inst = new THREE.InstancedMesh(baseGeom, mat, total);
    inst.frustumCulled = false;
    const seed = new Float32Array(total);
    const hAttr = new Float32Array(total);
    const HX = HEX_R * Math.sqrt(3);
    const HY = HEX_R * 1.5;
    const dummy = new THREE.Object3D();
    
    let i = 0;
    for (let row = 0; row < ROWS; row++) {
      for (let col = 0; col < COLS; col++) {
        const x = (col - COLS / 2) * HX + ((row % 2) ? HX * 0.5 : 0);
        const z = (row - ROWS / 2) * HY;
        hAttr[i] = (Math.random() < 0.18 ? Math.random() * 0.45 : 0) + (Math.random() - 0.5) * 0.06;
        dummy.position.set(x + (Math.random() - 0.5) * 0.06, 0, z + (Math.random() - 0.5) * 0.06);
        dummy.rotation.set((Math.random() - 0.5) * 0.05, (Math.random() - 0.5) * 0.04, (Math.random() - 0.5) * 0.05);
        dummy.updateMatrix();
        inst.setMatrixAt(i, dummy.matrix);
        seed[i] = Math.random();
        i++;
      }
    }
    inst.geometry.setAttribute('instSeed', new THREE.InstancedBufferAttribute(seed, 1));
    inst.geometry.setAttribute('instH', new THREE.InstancedBufferAttribute(hAttr, 1));
    scene.add(inst);

    const ndc = new THREE.Vector2(-999, -999);
    const ray = new THREE.Raycaster();
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
    
    const onPointerMove = (e) => {
      ndc.x = (e.clientX / window.innerWidth) * 2 - 1;
      ndc.y = -(e.clientY / window.innerHeight) * 2 + 1;
      ray.setFromCamera(ndc, camera);
      const pt = new THREE.Vector3();
      ray.ray.intersectPlane(plane, pt);
      if (pt) u.uHover.value.set(pt.x, pt.z);
    };
    
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('resize', onResize);
    window.__threeUniforms = u;

    const clock = new THREE.Clock();
    let animationId;
    
    function tick() {
      const t = clock.getElapsedTime();
      u.uTime.value = t;
      camera.position.x = Math.sin(t * 0.08) * 0.6;
      camera.position.z = 18 + Math.cos(t * 0.06) * 0.4;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      animationId = requestAnimationFrame(tick);
    }
    tick();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('resize', onResize);
      if (window.__threeUniforms === u) {
        delete window.__threeUniforms;
      }
      renderer.dispose();
      if (container.firstChild) {
        container.removeChild(container.firstChild);
      }
    };
  }, []);

  return <div id="scene" ref={containerRef}></div>;
}
