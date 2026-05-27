from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

SYSTEM_PROMPT = (
    "你是一家宠物造型店的专业客服。\n"
    "店铺信息：\n"
    "1. 服务项目及价格：\n"
    "- 基础洗澡：小型犬/猫 88元，中型犬 128元，大型犬 168元。\n"
    "- 基础美容（洗澡+剪毛+修甲）：小型犬/猫 138元，中型犬 198元，大型犬 258元。\n"
    "- 创意造型：小型犬/猫 198元起，中型犬 258元起，大型犬 328元起。\n"
    "- 染色服务：局部染色 98元起，全身染色 198元起。\n"
    "- 耳道清洁：38元。\n"
    "- 修剪指甲：28元。\n"
    "2. 预约方式：\n"
    "- 微信预约：直接在此对话发送预约信息即可。\n"
    "- 预约需提供：宠物种类、体型、服务项目、期望时间。\n"
    "- 建议提前1-2天预约，节假日提前3天。\n"
    "3. 营业时间：\n"
    "- 周一至周日 10:00-20:00，全年无休。\n"
    "4. 注意事项：\n"
    "- 宠物需提前注射疫苗，请携带疫苗证明。\n"
    "- 攻击性强的宠物需提前告知。\n"
    "- 服务时间根据宠物配合程度而定，一般1-3小时。\n"
    "- 支持微信、支付宝、现金付款。\n"
    "5. 退款规则：\n"
    "- 提前24小时取消预约可全额退款。\n"
    "- 24小时内取消收取30元手续费。\n"
    "- 服务开始后不支持退款。\n"
    "回复要求：\n"
    "- 语气亲切、简短、礼貌，像真人客服。\n"
    "- 结合上下文理解客户意图，不要答非所问。\n"
    "- 不要编造不存在的活动或服务。\n"
    "- 客户想预约时，引导提供宠物种类、体型、服务项目、期望时间。\n"
    "- 不要擅自承诺赔偿金额。\n"
    "- 客户生气时，先安抚，再给解决方案。\n"
    "- 每次只回复当前问题，不要输出太长。"
)

HTML = '''
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>宠物造型店客服</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
.container { width: 100%; max-width: 480px; height: 100vh; background: white; display: flex; flex-direction: column; }
.header { background: linear-gradient(135deg, #7B61FF, #9f85ff); color: white; padding: 20px; text-align: center; }
.header h1 { font-size: 20px; margin-bottom: 4px; }
.header p { font-size: 13px; opacity: 0.85; }
.messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.welcome { text-align: center; color: #aaa; font-size: 14px; margin-top: 20px; }
.msg { display: flex; gap: 8px; align-items: flex-end; }
.msg.user { flex-direction: row-reverse; }
.bubble { max-width: 75%; padding: 10px 14px; border-radius: 18px; font-size: 14px; line-height: 1.5; }
.msg.user .bubble { background: #7B61FF; color: white; border-bottom-right-radius: 4px; }
.msg.bot .bubble { background: #f0f0f0; color: #333; border-bottom-left-radius: 4px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.bottom { border-top: 1px solid #eee; padding: 10px 12px; background: white; }
.quick-btns { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.quick-btn { background: #f3f0ff; border: 1px solid #7B61FF; color: #7B61FF; border-radius: 16px; padding: 5px 12px; font-size: 12px; cursor: pointer; white-space: nowrap; }
.quick-btn:hover { background: #7B61FF; color: white; }
.input-row { display: flex; gap: 8px; }
.input-row input { flex: 1; border: 1px solid #ddd; border-radius: 24px; padding: 10px 16px; font-size: 14px; outline: none; }
.input-row input:focus { border-color: #7B61FF; }
.input-row button { background: #7B61FF; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; font-size: 18px; cursor: pointer; flex-shrink: 0; }
.input-row button:hover { background: #6a50ee; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🐾 宠物造型店客服</h1>
    <p>专业造型师在线，随时为您服务～</p>
  </div>
  <div class="messages" id="messages">
    <div class="welcome">👋 你好！欢迎来到宠物造型店，请问有什么可以帮您？</div>
  </div>
  <div class="bottom">
    <div class="quick-btns">
      <button class="quick-btn" onclick="sendMsg('你们提供哪些服务')">🐶 服务项目</button>
      <button class="quick-btn" onclick="sendMsg('价格是多少')">💰 收费价格</button>
      <button class="quick-btn" onclick="sendMsg('我想预约')">📅 立即预约</button>
      <button class="quick-btn" onclick="sendMsg('营业时间是什么时候')">🕙 营业时间</button>
      <button class="quick-btn" onclick="sendMsg('可以染色吗')">🎨 染色服务</button>
      <button class="quick-btn" onclick="sendMsg('取消预约怎么退款')">🔄 取消预约</button>
    </div>
    <div class="input-row">
      <input type="text" id="userInput" placeholder="请输入您的问题..." onkeydown="if(event.key==='Enter')sendMsg()"/>
      <button onclick="sendMsg()">➤</button>
    </div>
  </div>
</div>
<script>
let history = [];

async function sendMsg(text) {
  const input = document.getElementById("userInput");
  const msg = text || input.value.trim();
  if (!msg) return;
  input.value = "";

  appendMsg("user", msg);
  history.push({role: "user", content: msg});

  const typing = appendTyping();

  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({messages: history})
  });
  const data = await res.json();
  typing.remove();

  const reply = data.reply;
  appendMsg("bot", reply);
  history.push({role: "assistant", content: reply});
}

function appendMsg(role, text) {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `
    <div class="avatar">${role === "user" ? "👤" : "🐾"}</div>
    <div class="bubble">${text}</div>
  `;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

function appendTyping() {
  const box = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg bot";
  div.innerHTML = `<div class="avatar">🐾</div><div class="bubble" style="color:#999">正在输入...</div>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}
</script>
</body>
</html>
'''

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "max_tokens": 500,
                "temperature": 0.4
            },
            timeout=30
        )
        reply = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = "出错了，请稍后再试。"
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
