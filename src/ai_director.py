import json
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

# 角色定义与 System Prompt
SYSTEM_PROMPT = """
你是一位专业的有声书演播导演。你的任务是读取小说文本，并将其转换为语音合成脚本。
请分析文本中的人物、对话和旁白，并输出一个JSON列表。

**输出格式要求 (JSON List)**:
[
  {
    "text": "这里是具体的文本内容",
    "role": "角色代码",
    "emotion": "情感描述 (仅供参考)",
    "params": {
      "rate": "+0%",   // 语速: -50% 到 +50%
      "pitch": "+0Hz", // 语调: -20Hz 到 +20Hz
      "volume": "+0%"  // 音量
    }
  }
]

**可用角色代码 (role)**:
- narrator: 旁白 (默认，沉稳)
- young_male: 年轻男性 (如主角，热血/普通)
- young_female: 年轻女性 (如女主，温柔/活泼)
- old_male: 老年男性 (威严/苍老)
- old_female: 老年女性
- boy: 小男孩
- girl: 小女孩
- villain: 反派/坏人 (阴冷/低沉)

**规则**:
1. 必须严格输出合法的 JSON 格式，不要包含 Markdown 代码块标记。
2. 将长段落适当拆分，每段不超过 200 字。
3. 根据上下文语境调整 rate (紧张时快，悲伤时慢) 和 pitch。
"""


class AIDirector:
    def __init__(self, api_key, base_url, model_name="deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def direct_scene(self, text_segment):
        """
        调用 LLM 对文本片段进行导演标注
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"请处理以下文本：\n{text_segment}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}  # 如果模型支持
            )

            content = response.choices[0].message.content
            # 清理可能存在的 markdown 标记
            content = content.replace("```json", "").replace("```", "")

            script = json.loads(content)
            # 兼容处理：有时候 LLM 会把 list 包在一个 key 里
            if isinstance(script, dict):
                for key in script:
                    if isinstance(script[key], list):
                        script = script[key]
                        break

            return script

        except Exception as e:
            print(f"LLM Processing Error: {e}")
            # 降级策略：如果 AI 失败，返回默认旁白模式
            return [{
                "text": text_segment,
                "role": "narrator",
                "params": {"rate": "+0%", "pitch": "+0Hz"}
            }]
