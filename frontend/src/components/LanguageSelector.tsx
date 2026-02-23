import type { Language } from "../types";

interface Props {
  language: Language;
  onChange: (lang: Language) => void;
}

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "en", label: "EN" },
  { value: "fr", label: "FR" },
  { value: "sw", label: "SW" },
];

export function LanguageSelector({ language, onChange }: Props) {
  return (
    <div className="flex items-center gap-1">
      {LANGUAGES.map((lang) => (
        <button
          key={lang.value}
          onClick={() => onChange(lang.value)}
          className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
            language === lang.value
              ? "bg-relay-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          {lang.label}
        </button>
      ))}
    </div>
  );
}
