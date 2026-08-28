import { create } from 'zustand';

interface BookmarkStore {
  bookmarks: string[];
  toggle: (exerciseId: string) => void;
  isBookmarked: (exerciseId: string) => boolean;
}

export const useBookmarkStore = create<BookmarkStore>((set, get) => ({
  bookmarks: [],

  toggle: (exerciseId: string) => {
    set((state) => ({
      bookmarks: state.bookmarks.includes(exerciseId)
        ? state.bookmarks.filter((id) => id !== exerciseId)
        : [...state.bookmarks, exerciseId],
    }));
  },

  isBookmarked: (exerciseId: string) => {
    return get().bookmarks.includes(exerciseId);
  },
}));
