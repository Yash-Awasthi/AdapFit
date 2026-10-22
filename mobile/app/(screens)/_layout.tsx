/**
 * Detail screens live in their own stack, above the tab bar, so opening a tile
 * pushes a real screen: the tab you came from stays underneath and Back returns
 * to it instead of dropping the user on Today. A screen opened from a deep link
 * has no history, so its Back goes to the section that lists it.
 */
import { Stack, usePathname } from "expo-router";
import { colors } from "../../src/theme";
import { BackButton } from "../../src/components/BackButton";
import { sectionForRoute } from "../../src/navigation/sections";

function ScreensBack() {
  const pathname = usePathname();
  return <BackButton fallback={sectionForRoute(pathname)} />;
}

export default function ScreensLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerTitle: "",
        headerTransparent: true,
        headerShadowVisible: false,
        headerStyle: { backgroundColor: "transparent" },
        headerTintColor: colors.text.primary,
        headerLeft: () => <ScreensBack />,
        contentStyle: { backgroundColor: colors.bg.deep },
        animation: "slide_from_right",
      }}
    />
  );
}
