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

function encodePoint(point: LatLng): string {
  return `${point.lat},${point.lng}`;
}

export async function fetchRoutes(start: LatLng, end: LatLng): Promise<RoutesResponse> {
  const params = new URLSearchParams({
    start: encodePoint(start),
    end: encodePoint(end),
  });

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
