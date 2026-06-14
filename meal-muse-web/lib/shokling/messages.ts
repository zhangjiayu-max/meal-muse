/** 食灵场景化文案模板 */

type TimePeriod = "morning" | "noon" | "afternoon" | "evening" | "night";

function getTimePeriod(): TimePeriod {
  const h = new Date().getHours();
  if (h < 9) return "morning";
  if (h < 12) return "noon";
  if (h < 14) return "afternoon";
  if (h < 19) return "evening";
  return "night";
}

/** 随机取一条文案 */
function pick(messages: string[]): string {
  return messages[Math.floor(Math.random() * messages.length)];
}

/** 首页问候文案 */
export function getGreeting(nickname: string, hasRecord: boolean, streakDays: number, stageEmoji: string): string {
  const period = getTimePeriod();
  const timeGreetings: Record<TimePeriod, string[]> = {
    morning: ["早呀！新的一天从好吃的开始 ☀️", "早安！今天想吃什么呢？", "早上好呀，你的食灵已经醒了～"],
    noon: ["上午好！别忘了吃午餐哦 🍱", "记得按时吃饭！你的食灵在等你～"],
    afternoon: ["下午好！来点健康的下午茶吧 🫖", "加油！一天还没有记录饮食哦"],
    evening: ["晚上了！今天吃得怎么样呀 🌆", "晚餐时间到～今天有好好吃饭吗？"],
    night: ["这么晚了还没睡呀 🌙", "深夜了…你的食灵在打哈欠 😴", "记得早点休息，明天也要好好吃饭哦"],
  };

  if (hasRecord) {
    return `${pick(timeGreetings[period])} ${nickname}！今天已经记录了 ${streakDays > 0 ? `${streakDays} 天啦` : "很棒哦"} ${stageEmoji}`;
  }
  return `${pick(timeGreetings[period])} ${nickname}～今天还没记录呢，我等了一整天了😢`;
}

/** 记录后的反馈文案（基于营养分析） */
export function getRecordFeedback(
  calories: number,
  protein: number,
  carbs: number,
  fat: number,
  hasVegetable: boolean,
): { mood: "happy" | "embarrassed" | "fire" | "celebrate"; message: string } {
  const proteinOk = protein >= 20;
  const hasVeg = hasVegetable;

  if (proteinOk && hasVeg) {
    return {
      mood: "fire",
      message: pick([
        `💪 蛋白质 ${Math.round(protein)}g！你是懂营养的！`,
        `这搭配也太健康了吧！蛋白质在跳舞 💃`,
        `优质蛋白 + 蔬菜，完美搭配！继续保持 👏`,
      ]),
    };
  }
  if (calories > 800) {
    return {
      mood: "embarrassed",
      message: pick([
        `🔥 ${calories}kcal！这一餐热量有点高哦 😅`,
        `哇这一顿够猛的…偶尔放纵一下也可以啦～`,
        `热量炸弹 💣 不过开心最重要！明天吃清淡点就好`,
      ]),
    };
  }
  if (!proteinOk) {
    return {
      mood: "happy",
      message: pick([
        `记下来就好！下次可以加个蛋白质来源哦 💪`,
        `🍽️ 已记录！如果能再加点肉/蛋/豆腐就更均衡啦`,
        `收到！这一餐蛋白质不太够，建议补充一下～`,
      ]),
    };
  }
  return {
    mood: "happy",
    message: pick([
      `📝 记录成功！今天也在好好吃饭呢 🎉`,
      `收到收到！你的食灵记在小本本上了 ✍️`,
      `${calories}kcal！继续加油，保持好节奏 🌟`,
    ]),
  };
}

/** 空状态引导文案 */
export function getEmptyStateMessage(stageEmoji: string): { mood: "sad" | "happy"; message: string } {
  return {
    mood: "sad",
    message: pick([
      `${stageEmoji} "我等了一整天都没等到你…😢"`,
      `${stageEmoji} "好寂寞…今天还没人给我喂数据呢"`,
      `${stageEmoji} "今天还没记录！快告诉我你吃了什么！"`,
    ]),
  };
}

/** 连续记录里程碑文案 */
export function getStreakMessage(days: number): string | null {
  const milestones: Record<number, string[]> = {
    3: ["连续 3 天！习惯正在养成 💪", "3 天打卡！你已经超过了 50% 的人"],
    7: ["一周了！你打败了 90% 的人 🏆", "连续 7 天！食灵感受到了你的诚意 🥟"],
    14: ["两周！你已经是饮食达人了 🌿", "14 天！你的食灵正在茁壮成长"],
    30: ["一个月！你就是饮食管理大师 👑", "30 天不间断！太强了！🔥"],
  };
  const msgs = milestones[days];
  if (!msgs) return null;
  return pick(msgs);
}
