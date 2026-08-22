"""The use case: write today's postcard.

The retry loop splits the three layers cleanly: the application insists, the
infrastructure calls the model, and the domain decides whether what came back
is publishable. None of the three knows how the others do their job.
"""

from datetime import datetime

from domain.models import ECUADOR_TZ, Postcard
from domain.selection import choose_place, choose_tone
from domain.validation import review


class WritePostcard:
    def __init__(self, catalog, memory, weather, writer, archive, attempts=3):
        self._catalog = catalog
        self._memory = memory
        self._weather = weather
        self._writer = writer
        self._archive = archive
        self._attempts = attempts

    def execute(self, trigger: str):
        now = datetime.now(ECUADOR_TZ)
        print(f"[agent] waking up. trigger={trigger} local_time={now.isoformat()}")

        memory = self._memory.recent()
        print(f"[memory] {len(memory)} previous postcards in the history")

        place = choose_place(memory, self._catalog)
        tone = choose_tone(memory)
        print(f"[decision] place={place.name} tone={tone}")

        weather = self._weather.fetch(place)
        print(f"[weather] {place.name}: {weather.temperature}C, {weather.description}, "
              f"humidity {weather.humidity}%, wind {weather.wind}km/h")

        draft = self._insist_until_it_works(place, weather, tone, memory)

        postcard = Postcard(
            id=now.strftime("%Y-%m-%dT%H-%M-%S"),
            epoch=int(now.timestamp()),
            place=place.name,
            province=place.province,
            title=draft.title or "Untitled",
            text=draft.text,
            tone=tone,
            weather=weather,
            generated_at=now.isoformat(),
            trigger=trigger,
            model=self._writer.model,
        )
        self._memory.save(postcard)

        total = self._archive.publish(self._memory.all())
        print(f"[agent] done. '{postcard.title}' from {postcard.place}. archive: {total} postcards")

        return {
            "statusCode": 200,
            "postcard_id": postcard.id,
            "place": postcard.place,
            "title": postcard.title,
            "archive_total": total,
        }

    def _insist_until_it_works(self, place, weather, tone, memory):
        last = None

        for attempt in range(1, self._attempts + 1):
            draft = self._writer.write(place, weather, tone, memory, attempt)
            if draft is None:
                continue

            failures = review(draft, place, tone)
            last = draft
            if not failures:
                print(f"[validation] attempt {attempt}: postcard accepted")
                return draft
            print(f"[validation] attempt {attempt} rejected: {', '.join(failures)}")

        if last and last.text:
            print("[validation] attempts exhausted, publishing the best available")
            return last
        raise ValueError("the model produced no usable postcard in any attempt")
