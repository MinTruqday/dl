"use client";
import { useCallback, useEffect, useState } from "react";
import { qaApi } from "../services/qa.service";
import { messageOf } from "../lib/qa";

export function useProject(projectId) {
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setProject(await qaApi.getProject(projectId));
    } catch (reason) {
      setError(messageOf(reason));
    } finally {
      setLoading(false);
    }
  }, [projectId]);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { project, loading, error, setError, reload };
}
