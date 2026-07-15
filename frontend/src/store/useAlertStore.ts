import { create } from "zustand";
import type { Alert, Camera, EventItem } from "@/lib/api";

type AlertStore = {
  alerts: Alert[];
  cameras: Camera[];
  events: EventItem[];
  liveConnected: boolean;
  eventsLiveConnected: boolean;
  setAlerts: (alerts: Alert[]) => void;
  prependAlert: (alert: Alert) => void;
  setCameras: (cameras: Camera[]) => void;
  setEvents: (events: EventItem[]) => void;
  prependEvent: (event: EventItem) => void;
  setLiveConnected: (connected: boolean) => void;
  setEventsLiveConnected: (connected: boolean) => void;
  updateAlert: (alert: Alert) => void;
};

export const useAlertStore = create<AlertStore>((set) => ({
  alerts: [],
  cameras: [],
  events: [],
  liveConnected: false,
  eventsLiveConnected: false,
  setAlerts: (alerts) => set({ alerts }),
  prependAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts.filter((a) => a.id !== alert.id)],
    })),
  setCameras: (cameras) => set({ cameras }),
  setEvents: (events) => set({ events }),
  prependEvent: (event) =>
    set((state) => ({
      events: [event, ...state.events.filter((e) => e.id !== event.id)].slice(0, 50),
    })),
  setLiveConnected: (liveConnected) => set({ liveConnected }),
  setEventsLiveConnected: (eventsLiveConnected) => set({ eventsLiveConnected }),
  updateAlert: (alert) =>
    set((state) => ({
      alerts: state.alerts.map((a) => (a.id === alert.id ? alert : a)),
    })),
}));
