import assemblyai as aai
from django.conf import settings


class TranscriptionService:
    """Transcribe call recordings and analyze sentiment using AssemblyAI."""

    @staticmethod
    def transcribe_call(call_log):
        """
        Transcribe a call recording and store text + sentiment on the CallLog.
        Requires call_log.recording_url to be set.
        """
        if not settings.ASSEMBLYAI_API_KEY:
            call_log.transcription_status = 'no_api_key'
            call_log.save(update_fields=['transcription_status'])
            return None

        if not call_log.recording_url:
            call_log.transcription_status = 'no_recording'
            call_log.save(update_fields=['transcription_status'])
            return None

        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY

        config = aai.TranscriptionConfig(
            sentiment_analysis=True,
        )

        try:
            call_log.transcription_status = 'processing'
            call_log.save(update_fields=['transcription_status'])

            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(call_log.recording_url)

            if transcript.status == aai.TranscriptStatus.error:
                call_log.transcription_status = 'failed'
                call_log.save(update_fields=['transcription_status'])
                return None

            # Store transcription text
            call_log.transcription_text = transcript.text or ''

            # Aggregate sentiment from sentiment analysis results
            sentiment_label, sentiment_score = TranscriptionService._aggregate_sentiment(transcript)
            call_log.sentiment = sentiment_label
            call_log.sentiment_score = sentiment_score
            call_log.transcription_status = 'completed'

            call_log.save(update_fields=[
                'transcription_text',
                'sentiment',
                'sentiment_score',
                'transcription_status',
            ])

            return transcript.text

        except Exception as e:
            call_log.transcription_status = 'failed'
            call_log.save(update_fields=['transcription_status'])
            return None

    @staticmethod
    def _aggregate_sentiment(transcript):
        """
        Roll up per-sentence sentiment into one overall label and score.
        Returns (label, score) where score is -1.0 (negative) to 1.0 (positive).
        """
        results = getattr(transcript, 'sentiment_analysis', None) or []
        if not results:
            return '', None

        score_map = {'POSITIVE': 1, 'NEUTRAL': 0, 'NEGATIVE': -1}
        total = 0
        count = 0
        for r in results:
            total += score_map.get(r.sentiment.value if hasattr(r.sentiment, 'value') else str(r.sentiment), 0)
            count += 1

        if count == 0:
            return '', None

        avg = total / count

        if avg > 0.2:
            label = 'positive'
        elif avg < -0.2:
            label = 'negative'
        else:
            label = 'neutral'

        return label, round(avg, 3)