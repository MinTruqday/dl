import { useState, useRef, useEffect } from "react";

export function useAudioRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [isRecordingPaused, setIsRecordingPaused] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, []);

  const handleStartRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setIsRecordingPaused(false);
      setRecordingDuration(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error("Lỗi truy cập micro", err);
    }
  };

  const handleTogglePauseRecording = () => {
    if (mediaRecorder && isRecording) {
      if (isRecordingPaused) {
        mediaRecorder.resume();
        setIsRecordingPaused(false);
        recordingTimerRef.current = setInterval(() => {
          setRecordingDuration((prev) => prev + 1);
        }, 1000);
      } else {
        mediaRecorder.pause();
        setIsRecordingPaused(true);
        if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      }
    }
  };

  const handleStopRecording = (): Promise<File | null> => {
    return new Promise((resolve) => {
      if (mediaRecorder && isRecording) {
        mediaRecorder.onstop = () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
          const file = new File([audioBlob], "voice_message.webm", { type: "audio/webm" });
          setIsRecording(false);
          setIsRecordingPaused(false);
          setRecordingDuration(0);
          if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
          mediaRecorder.stream.getTracks().forEach((track) => track.stop());
          resolve(file);
        };
        mediaRecorder.stop();
      } else {
        resolve(null);
      }
    });
  };

  const handleCancelRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setIsRecordingPaused(false);
      setRecordingDuration(0);
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
      mediaRecorder.stream.getTracks().forEach((track) => track.stop());
    }
  };

  return {
    isRecording,
    isRecordingPaused,
    recordingDuration,
    handleStartRecording,
    handleTogglePauseRecording,
    handleStopRecording,
    handleCancelRecording
  };
}
