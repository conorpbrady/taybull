from datetime import datetime

class DecisionEngine:

    def __init__(self):
        pass

    def select_preferred_time(self, times):
        ranked_times = self.rank_by_time(times)
        return ranked_times[0]

    def rank_by_time(self, times, weekend_only = False):
        # TODO: Filter on type, prefer indoor / dining room when possible

        # 20:00 is ideal dinner time, choose reservation based of closeness to that
        today = datetime.today()

        ideal = '20:00:00'
        time_fmt = '%H:%M:%S'
        ranks = {}
        for t in times:
            score = 0
            day, time = t.split(' ')
            day_delta = datetime.fromisoformat(day) - today
            score += day_delta.days * 1000
            #print(time, ideal)
            time_delta = datetime.strptime(time, time_fmt) - datetime.strptime(ideal, time_fmt)
            minutes = time_delta.seconds / 60
            #print(minutes)

            # If res time is before ideal time, subtract 1 day (1440 min) to have direct comparison to later times
            # subtract 5 from score to favor earlier times over later
            if minutes > 1200:
                minutes =  1440 - minutes - 5

            score += minutes
            ranks[t] = score

        return [k for k, v in sorted(ranks.items(), key=lambda item: item[1])]
