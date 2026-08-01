"use client";

import { Heart, Laugh, ThumbsUp } from "lucide-react";

const reactionOptions = [
  { id: "like", label: "Thích", icon: ThumbsUp },
  { id: "heart", label: "Quan tâm", icon: Heart },
  { id: "laugh", label: "Vui", icon: Laugh },
];

export default function MessageReactions({
  reactions = [],
  react,
}: {
  reactions?: Array<{ reaction?: string }>;
  react: (reaction: string) => void;
}) {
  const counts = reactionOptions.map((option) => ({
    ...option,
    count: reactions.filter((item) => item.reaction === option.id).length,
  }));

  return (
    <div className="flex flex-wrap items-center gap-1">
      {counts
        .filter((option) => option.count > 0)
        .map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => react(option.id)}
            aria-label={`${option.label}, ${option.count}`}
            className="inline-flex h-7 items-center gap-1 rounded-full border border-current/20 px-2 text-[11px] opacity-80 hover:opacity-100"
          >
            <option.icon size={13} strokeWidth={1.8} />
            {option.count}
          </button>
        ))}
      <div className="flex items-center rounded-full border border-current/15 bg-transparent p-0.5 opacity-0 transition group-hover:opacity-80 group-focus-within:opacity-80">
        {reactionOptions.map((option) => (
          <button
            key={option.id}
            type="button"
            onClick={() => react(option.id)}
            aria-label={option.label}
            className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-current/10"
          >
            <option.icon size={14} strokeWidth={1.8} />
          </button>
        ))}
      </div>
    </div>
  );
}
