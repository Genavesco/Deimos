import { Canvas, useFrame, useLoader } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { Suspense, useMemo, useRef } from "react";
import * as THREE from "three";
import earthColorMapUrl from "../assets/earth/earth_color.jpg";
import earthNormalMapUrl from "../assets/earth/earth_normal.jpg";

type Zones = {
  craterKm?: number;
  shockKm?: number;
  thermalKm?: number;
};

const EARTH_RADIUS_KM = 6371;

const latLonToCartesian = (lat: number, lon: number, radius: number) => {
  const latRad = THREE.MathUtils.degToRad(lat);
  const lonRad = THREE.MathUtils.degToRad(lon);
  const cosLat = Math.cos(latRad);
  const x = radius * cosLat * Math.cos(lonRad);
  const y = radius * Math.sin(latRad);
  const z = radius * cosLat * Math.sin(lonRad);
  return new THREE.Vector3(x, y, z);
};

function buildRingOnSphere(centerDir: THREE.Vector3, alphaRad: number, thicknessKm: number, color: string, opacity = 0.35) {
  const R = 1; // unit sphere
  const halfThick = Math.max(0.5, thicknessKm) / EARTH_RADIUS_KM; // radians
  const innerAlpha = Math.max(0.0005, alphaRad - halfThick / 2);
  const outerAlpha = Math.max(innerAlpha + 0.00025, alphaRad + halfThick / 2);

  const innerR = Math.sin(innerAlpha) * R;
  const outerR = Math.sin(outerAlpha) * R;
  const distance = Math.cos(alphaRad) * R;

  const geom = new THREE.RingGeometry(innerR, outerR, 256, 1);
  const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), centerDir.clone().normalize());
  geom.applyQuaternion(quat);
  geom.translate(centerDir.x * distance, centerDir.y * distance, centerDir.z * distance);

  const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity, side: THREE.DoubleSide });
  return new THREE.Mesh(geom, mat);
}

function Earth({ lat, lon, zones }: { lat: number; lon: number; zones?: Zones }) {
  const [colorMap, normalMap] = useLoader(THREE.TextureLoader, [earthColorMapUrl, earthNormalMapUrl]);

  const groupRef = useRef<THREE.Group>(null);
  const earthMaterial = useMemo(() => {
    const mat = new THREE.MeshStandardMaterial({
      map: colorMap,
      normalMap,
      roughness: 0.6,
      metalness: 0.02,
    });
    colorMap.colorSpace = THREE.SRGBColorSpace;
    colorMap.needsUpdate = true;
    normalMap.needsUpdate = true;
    return mat;
  }, [colorMap, normalMap]);

  const centerDir = useMemo(() => latLonToCartesian(lat, lon, 1).normalize(), [lat, lon]);
  const ringMeshes = useMemo(() => {
    if (!zones) return [] as THREE.Mesh[];
    const meshes: THREE.Mesh[] = [];
    const defThickness = 30; // km
    if (zones.craterKm && zones.craterKm > 0) {
      const alpha = zones.craterKm / EARTH_RADIUS_KM;
      meshes.push(buildRingOnSphere(centerDir, alpha, Math.max(10, defThickness), "#ff3b30", 0.45));
    }
    if (zones.shockKm && zones.shockKm > 0) {
      const alpha = zones.shockKm / EARTH_RADIUS_KM;
      meshes.push(buildRingOnSphere(centerDir, alpha, defThickness * 1.2, "#ff9f0a", 0.35));
    }
    if (zones.thermalKm && zones.thermalKm > 0) {
      const alpha = zones.thermalKm / EARTH_RADIUS_KM;
      meshes.push(buildRingOnSphere(centerDir, alpha, defThickness * 1.2, "#ffd60a", 0.3));
    }
    return meshes;
  }, [centerDir, zones]);

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.1;
    }
  });

  return (
    <group ref={groupRef} rotation={[0, -Math.PI / 2, 0]}>
      <mesh castShadow receiveShadow material={earthMaterial}>
        <sphereGeometry args={[1, 128, 128]} />
      </mesh>
      {ringMeshes.map((m, i) => (
        <primitive key={i} object={m} />
      ))}
      <mesh position={centerDir.clone().multiplyScalar(1.02)}>
        <sphereGeometry args={[0.02, 32, 32]} />
        <meshBasicMaterial color="#ff3b30" />
      </mesh>
      <directionalLight position={[3, 2, 2]} intensity={1.6} />
      <ambientLight intensity={0.25} />
    </group>
  );
}

export default function EarthImpactPreview({ lat, lon, craterKm, shockKm, thermalKm }: { lat: number; lon: number; craterKm?: number; shockKm?: number; thermalKm?: number }) {
  const zones = useMemo(() => ({ craterKm, shockKm, thermalKm }), [craterKm, shockKm, thermalKm]);
  return (
    <div className="rounded-xl border border-white/10 bg-neutral-950/90 shadow-lg overflow-hidden">
      <Canvas camera={{ position: [2.4, 1.8, 2.4], fov: 40 }} shadows>
        <color attach="background" args={["#03040a"]} />
        <Suspense fallback={null}>
          <Earth lat={lat} lon={lon} zones={zones} />
          <Stars radius={6} depth={20} count={6000} factor={0.2} fade />
        </Suspense>
        <OrbitControls enablePan autoRotate autoRotateSpeed={0.5} enableZoom />
      </Canvas>
    </div>
  );
}
