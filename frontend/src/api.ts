export type LatLng = {
  lat: number;
  lng: number;
};

export type RouteOption = {
  id: string;
  distanceMeters: number;
  durationSeconds: number;
  coordinates: [number, number][];
};

export type RoutesResponse = {
  routes: RouteOption[];
};

export async function fetchRoutes(waypoints: LatLng[]): Promise<RoutesResponse> {
  const params = new URLSearchParams();
  for (const wp of waypoints) {
    params.append('waypoints', `${wp.lat},${wp.lng}`);
  }

  const response = await fetch(`/api/routes?${params.toString()}`);
  if (!response.ok) {
    let message = 'Route request failed';
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json() as Promise<RoutesResponse>;
}
