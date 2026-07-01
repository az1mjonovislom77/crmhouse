class CDRDedupService:

    @staticmethod
    def should_skip(item, seen_sessions):

        disposition = item.get("disposition")

        if disposition != "NO ANSWER":
            return False

        recording = item.get("recordingfile")

        if not recording:
            return False

        if recording in seen_sessions:
            return True

        seen_sessions.add(recording)

        return False