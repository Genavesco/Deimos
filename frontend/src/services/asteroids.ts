export async function fetchAsteroids(q?: string) {
  const url = q ? `/asteroids?q=${encodeURIComponent(q)}` : `/asteroids`;
  const res = await fetch(url);
  return res.json();
}

export async function fetchAsteroidDetail(id: string) {
  const res = await fetch(`/asteroids/${id}`);
  return res.json();
}
