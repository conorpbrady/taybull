from datetime import datetime

class DecisionEngine:

    def __init__(self, prefs, log):
        self.ideal = prefs.ideal_time
        self.weekday_prefs = [
                prefs.sun_rank,
                prefs.mon_rank,
                prefs.tue_rank,
                prefs.wed_rank,
                prefs.thu_rank,
                prefs.fri_rank,
                prefs.sat_rank
                ]
        self.specific_date_flag = prefs.specific_date_flag
        self.specific_date = prefs.specific_date
        self.log = log

    def rank_by_time(self, times):

        today = datetime.today()
        if self.specific_date_flag:
            self.log.append(f'specific date {self.specific_date.strftime("%Y-%m-%d")} set')
        time_fmt = '%H:%M:%S'
        ranks = {}
        for time_slot in times.keys():
            score = 0
            time_slot_dt = datetime.strptime(time_slot, '%Y-%m-%d %H:%M:%S')
            if self.specific_date_flag:
                if time_slot_dt.date() != self.specific_date:
                    continue

            day_delta = time_slot_dt - today
            score += day_delta.days * 1000
            #print(time, ideal)
            time_delta = time_slot_dt - datetime.strptime(self.ideal, '%H:%M')
            minutes = time_delta.seconds / 60
            #print(minutes)

            # If res time is before ideal time, subtract 1 day (1440 min) to have direct comparison to later times
            # subtract 5 from score to favor earlier times over later
            if minutes > 1200:
                minutes =  1440 - minutes - 5

            # Add score for day of week preference

            # 0 - Sunday -- 6 - Saturday
            dow_index = int(time_slot_dt.strftime('%w'))
            dow_multiplier = self.weekday_prefs[dow_index]

            score += minutes
            if dow_multiplier != 0:
                score *= (10 - dow_multiplier)
                ranks[time_slot] = score
        self.log.append(f'found {len(ranks)} times after preferences')
        return [k for k, v in sorted(ranks.items(), key=lambda item: item[1])]
