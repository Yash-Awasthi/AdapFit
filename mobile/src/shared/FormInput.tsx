/**
 * FormInput — labelled text input with icon, focus state, and error handling.
 * Directly inspired by the school-teacher-app's FormInput pattern.
 */

import { MaterialCommunityIcons } from "@expo/vector-icons";
import React, { useState } from "react";
import { StyleSheet, Text, TextInput, View, ViewStyle, TouchableOpacity } from "react-native";
import { COLORS } from "./styles";

type IconName = React.ComponentProps<typeof MaterialCommunityIcons>["name"];

interface FormInputProps {
  icon?: IconName;
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (v: string) => void;
  secureTextEntry?: boolean;
  rightIcon?: IconName;
  onRightIconPress?: () => void;
  autoCapitalize?: "none" | "sentences" | "words" | "characters";
  autoCorrect?: boolean;
  error?: string;
  keyboardType?: "default" | "numeric" | "email-address" | "phone-pad";
  multiline?: boolean;
  numberOfLines?: number;
  style?: ViewStyle;
}

export function FormInput({
  icon,
  label,
  placeholder,
  value,
  onChangeText,
  secureTextEntry = false,
  rightIcon,
  onRightIconPress,
  autoCapitalize = "sentences",
  autoCorrect = true,
  error,
  keyboardType = "default",
  multiline = false,
  numberOfLines = 1,
  style,
}: FormInputProps) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={[styles.inputGroup, style]}>
      <Text style={styles.inputLabel}>{label}</Text>

      <View style={[styles.inputContainer, focused && styles.inputContainerFocused, error && styles.inputContainerError]}>
        {icon && (
          <MaterialCommunityIcons
            name={icon}
            size={19}
            color={focused ? COLORS.accent : COLORS.textMuted}
            style={styles.inputIcon}
          />
        )}

        <TextInput
          style={[styles.textInput, multiline && styles.textInputMultiline]}
          placeholder={placeholder}
          placeholderTextColor="#475569"
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={secureTextEntry}
          autoCapitalize={autoCapitalize}
          autoCorrect={autoCorrect}
          keyboardType={keyboardType}
          multiline={multiline}
          numberOfLines={numberOfLines}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          accessibilityLabel={label}
        />

        {rightIcon && (
          <TouchableOpacity
            onPress={onRightIconPress}
            style={styles.rightIconBtn}
            hitSlop={8}
            accessibilityRole="button"
          >
            <MaterialCommunityIcons name={rightIcon} size={19} color={COLORS.textMuted} />
          </TouchableOpacity>
        )}
      </View>

      {error && <Text style={styles.fieldError}>{error}</Text>}
    </View>
  );
}

interface SearchInputProps {
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
}

export function SearchInput({ value, onChangeText, placeholder = "Search..." }: SearchInputProps) {
  const [focused, setFocused] = useState(false);

  return (
    <View style={[styles.searchContainer, focused && styles.inputContainerFocused]}>
      <MaterialCommunityIcons name="magnify" size={20} color={COLORS.textMuted} />
      <TextInput
        style={styles.searchInput}
        placeholder={placeholder}
        placeholderTextColor="#475569"
        value={value}
        onChangeText={onChangeText}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
      />
      {value.length > 0 && (
        <TouchableOpacity onPress={() => onChangeText("")}>
          <MaterialCommunityIcons name="close-circle" size={18} color={COLORS.textMuted} />
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: COLORS.textSecondary,
    marginLeft: 2,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.input,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.inputBorder,
    height: 52,
    paddingHorizontal: 14,
    gap: 10,
  },
  inputContainerFocused: {
    borderColor: COLORS.inputFocus,
    backgroundColor: COLORS.surface,
  },
  inputContainerError: {
    borderColor: COLORS.danger,
  },
  inputIcon: {
    flexShrink: 0,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
    paddingVertical: 0,
  },
  textInputMultiline: {
    minHeight: 80,
    textAlignVertical: "top",
    paddingTop: 12,
  },
  rightIconBtn: {
    padding: 2,
  },
  fieldError: {
    color: COLORS.danger,
    fontSize: 12,
    marginTop: 2,
    marginLeft: 2,
  },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: COLORS.input,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: COLORS.inputBorder,
    height: 44,
    paddingHorizontal: 12,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
  },
});
