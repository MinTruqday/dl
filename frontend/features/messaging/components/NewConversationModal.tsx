"use client";

import { useState } from "react";
import { Button } from "@/shared/components/ui/Button";
import {
  Modal,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
} from "@/shared/components/ui/Modal";
export default function NewConversationModal({
  open,
  close,
  findUsers,
  start,
  createGroup,
}: {
  open: boolean;
  close: () => void;
  findUsers: (query: string) => Promise<any[]>;
  start: (person: any) => void;
  createGroup: (name: string, ids: string[]) => Promise<boolean>;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [groupName, setGroupName] = useState("");
  const search = async () => setResults(await findUsers(query));
  const choose = (person: any) => {
    const id = person._id ?? person.id;
    setSelected((rows) =>
      rows.includes(id) ? rows.filter((item) => item !== id) : [...rows, id],
    );
  };
  const create = async () => {
    if (await createGroup(groupName, selected)) close();
  };
  return (
    <Modal isOpen={open} onClose={close}>
      <ModalHeader>
        <ModalTitle>Cuộc trò chuyện mới</ModalTitle>
      </ModalHeader>
      <ModalContent>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="apple-input min-w-0 flex-1"
            placeholder="Tên hoặc email"
          />
          <Button variant="secondary" disabled={!query.trim()} onClick={search}>
            Tìm
          </Button>
        </div>
        <ul className="mt-4 max-h-64 divide-y divide-border overflow-y-auto">
          {results.map((person) => {
            const id = person._id ?? person.id;
            return (
              <li
                key={id}
                className="flex items-center justify-between gap-4 py-3"
              >
                <button
                  className="min-w-0 flex-1 truncate text-left text-[14px] font-semibold text-ink"
                  onClick={() => {
                    start(person);
                    close();
                  }}
                >
                  {person.full_name || person.email || person.slug}
                </button>
                <label className="flex items-center gap-2 text-[12px] text-ink-muted">
                  <input
                    type="checkbox"
                    checked={selected.includes(id)}
                    onChange={() => choose(person)}
                    className="accent-[hsl(var(--brand))]"
                  />
                  Chọn nhóm
                </label>
              </li>
            );
          })}
        </ul>
        {selected.length > 1 && (
          <div className="mt-5 border-t border-border pt-4">
            <label
              htmlFor="group-name"
              className="mb-2 block text-[13px] font-semibold text-ink"
            >
              Tên nhóm
            </label>
            <input
              id="group-name"
              value={groupName}
              onChange={(event) => setGroupName(event.target.value)}
              className="apple-input w-full"
            />
          </div>
        )}
      </ModalContent>
      <ModalFooter>
        <Button variant="secondary" onClick={close}>
          Đóng
        </Button>
        {selected.length > 1 && (
          <Button disabled={!groupName.trim()} onClick={create}>
            Tạo nhóm
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
}
