import * as THREE from "three";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, ContactShadows } from "@react-three/drei";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { createNoise3D } from "simplex-noise";
import * as BufferGeometryUtils from "three/examples/jsm/utils/BufferGeometryUtils.js";

function mulberry32(a: number) {
  let t = a >>> 0;
  return function () {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function fbm3D(
  noise3D: (x: number, y: number, z: number) => number,
  x: number,
  y: number,
  z: number,
  oct = 5,
  lac = 2,
  gain = 0.5,
) {
  let amp = 1;
  let freq = 1;
  let sum = 0;
  let norm = 0;
  for (let i = 0; i < oct; i++) {
    sum += amp * noise3D(x * freq, y * freq, z * freq);
    norm += amp;
    amp *= gain;
    freq *= lac;
  }
  return sum / Math.max(norm, 1e-6);
}

function makeAsteroid(seed: number) {
  let geom: THREE.BufferGeometry = new THREE.IcosahedronGeometry(1, 7);
  geom = BufferGeometryUtils.mergeVertices(geom, 1e-5);

  const positionAttr = geom.getAttribute("position") as THREE.BufferAttribute;
  const rng = mulberry32(Math.floor(seed) || 1);
  const noise3D = createNoise3D(rng);
  const v = new THREE.Vector3();

  const baseR = 1.0;
  const amp = 0.22;
  const freq = 1.45;
  const microAmp = 0.07;
  const microFreq = 6.5;

  for (let i = 0; i < positionAttr.count; i++) {
    v.fromBufferAttribute(positionAttr, i).normalize();
    const nLow = fbm3D(noise3D, v.x * freq, v.y * freq, v.z * freq, 5, 2, 0.5);
    const nHigh = fbm3D(noise3D, v.x * microFreq, v.y * microFreq, v.z * microFreq, 3, 2, 0.5);
    const ns = Math.tanh(nLow * 1.2);
    let r = baseR * (1 + amp * ns + microAmp * nHigh);
    r = THREE.MathUtils.clamp(r, 0.84, 1.28);
    v.multiplyScalar(r);
    positionAttr.setXYZ(i, v.x, v.y, v.z);
  }
  positionAttr.needsUpdate = true;

  geom.computeVertexNormals();

  const colors = new Float32Array(positionAttr.count * 3);
  const colorA = new THREE.Color("#4f4943");
  const colorB = new THREE.Color("#7f6a55");
  const colorC = new THREE.Color("#d3c4ab");
  const p = new THREE.Vector3();

  for (let i = 0; i < positionAttr.count; i++) {
    positionAttr.setXYZ(i, positionAttr.getX(i), positionAttr.getY(i), positionAttr.getZ(i));
    p.fromBufferAttribute(positionAttr, i).normalize();
    const coarse = fbm3D(noise3D, p.x * 3.4 + 3.1, p.y * 3.4 - 1.7, p.z * 3.4 + 0.9, 4, 2.2, 0.55);
    const fine = fbm3D(noise3D, p.x * 8.1 - 5.4, p.y * 8.1 + 2.8, p.z * 8.1 - 7.6, 3, 2.1, 0.6);
    const dust = fbm3D(noise3D, p.x * 13.0 + 9.3, p.y * 13.0 - 4.7, p.z * 13.0 + 6.2, 2, 2.0, 0.7);

    const baseMix = THREE.MathUtils.clamp(0.55 + 0.45 * coarse, 0, 1);
    const dustMix = THREE.MathUtils.clamp(0.5 + 0.5 * dust, 0, 1);
    const craterMix = THREE.MathUtils.clamp(0.5 - 0.5 * fine, 0, 1);

    const base = colorA.clone().lerp(colorB, baseMix);
    const dusty = base.clone().lerp(colorC, dustMix * 0.6);
    const final = dusty.lerp(colorA.clone().multiplyScalar(0.5), craterMix * 0.4);

    colors[i * 3 + 0] = final.r;
    colors[i * 3 + 1] = final.g;
    colors[i * 3 + 2] = final.b;
  }

  geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  return geom;
}

function Rock({ seed }: { seed: number }) {
  const geometry = useMemo(() => makeAsteroid(seed), [seed]);
  const meshRef = useRef<THREE.Mesh>(null);
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        vertexColors: true,
        roughness: 0.82,
        metalness: 0.08,
        envMapIntensity: 1.0,
      }),
    [],
  );

  useEffect(() => () => {
    geometry.dispose();
    material.dispose();
  }, [geometry, material]);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.18;
      meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, 0.26, 0.02);
    }
  });

  return <mesh ref={meshRef} geometry={geometry} material={material} castShadow receiveShadow />;
}

export default function Builder3D() {
  const [seed, setSeed] = useState(42);

  return (
    <div className="bg-black/40 rounded p-2">
      <Canvas
        style={{ height: 320, borderRadius: 12 }}
        shadows
        gl={{ antialias: true }}
        camera={{ position: [2.6, 1.8, 2.6], fov: 40 }}
        onCreated={({ gl }) => {
          const renderer = gl as THREE.WebGLRenderer & {
            outputColorSpace?: THREE.ColorSpace;
            physicallyCorrectLights?: boolean;
          };

          if (typeof renderer.physicallyCorrectLights === "boolean") {
            renderer.physicallyCorrectLights = true;
          }

          (renderer as any).toneMapping = THREE.ACESFilmicToneMapping;
          (renderer as any).toneMappingExposure = 1.05;

          if ("outputColorSpace" in renderer) {
            renderer.outputColorSpace = (THREE as any).SRGBColorSpace ?? renderer.outputColorSpace;
          }
        }}
      >
        <color attach="background" args={["#060708"]} />
        <ambientLight intensity={0.35} />
        <directionalLight
          position={[4, 4, 3]}
          intensity={1.45}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <pointLight position={[-3, 2, -2]} intensity={0.35} color="#b7b4ff" />
        <Suspense fallback={null}>
          <Rock seed={seed} />
          <Environment preset="sunset" />
        </Suspense>
        <ContactShadows position={[0, -1.2, 0]} opacity={0.45} scale={6} blur={2.6} far={2} />
        <OrbitControls enablePan={false} enableDamping dampingFactor={0.08} minDistance={1.5} maxDistance={4.5} />
      </Canvas>
      <div className="mt-3 flex gap-2 justify-between text-sm">
        <button
          className="px-3 py-1.5 bg-neutral-900 rounded border border-white/10 hover:border-white/25"
          onClick={() => setSeed(Math.floor(Math.random() * 1e9))}
        >
          Asteroide aleatorio
        </button>
        <span className="text-neutral-400">Arrastra para rotar y usa la rueda para acercar</span>
      </div>
    </div>
  );
}
