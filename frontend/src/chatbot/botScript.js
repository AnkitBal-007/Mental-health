/**
 * Bot conversation flows for the MindGuard Chatbot.
 *
 * Design principles:
 * - Non-clinical, warm, conversational tone
 * - No alarming terminology (no "distress", "score", "crisis")
 * - Questions cycle through multiple topics: sleep, mood, safety, support, daily life
 * - Bilingual: English + Hindi (Devanagari)
 */

export const BOT_NAME = 'Saheli Didi';  // Elder Sister persona

export const WELCOME_MESSAGES = {
  en: [
    `Namaste 🙏 I'm **${BOT_NAME}**, your elder sister here for you.`,
    `Whatever is on your mind, you can share it with me without any fear. You don't have to face anything alone — I'm right here with you.`,
    `Tell me — **how are you feeling right now? Has something been weighing on your heart?**`,
  ],
  hi: [
    `नमस्ते 🙏 मैं **${BOT_NAME}** हूँ, तुम्हारी बड़ी दीदी।`,
    `जो भी तुम्हारे मन में हो, बिना किसी डर या झिझक के मुझसे कहो। तुम्हें अकेले कुछ भी नहीं सहना है — मैं हमेशा तुम्हारे साथ हूँ।`,
    `मुझे बताओ — **आज तुम्हारा मन कैसा है? क्या कोई बात तुम्हें परेशान कर रही है?**`,
  ],
};

export const FOLLOW_UP_QUESTIONS = {
  en: [
    "How has your sleep been lately? Are you getting enough rest?",
    "Have you been able to eat well and take care of yourself these days?",
    "Is there anything that's been worrying you or making you feel uneasy?",
    "Have you been able to spend time with people you trust — family or friends?",
    "On a scale from 1 to 5, how would you describe your overall mood today? (1 = very low, 5 = good)",
    "Is there anything specific you'd like support with right now?",
    "Have you felt safe at home and in your neighbourhood recently?",
    "Is there anything else you'd like to share with me today?",
  ],
  hi: [
    "आजकल आपकी नींद कैसी है? क्या आप ठीक से सो पा रही हैं?",
    "खाना-पीना ठीक है? अपना ख्याल रख पा रही हैं?",
    "कोई बात है जो आपको परेशान कर रही हो या बेचैन महसूस करा रही हो?",
    "क्या आप अपने परिवार या किसी करीबी के साथ समय बिता पा रही हैं?",
    "1 से 5 के पैमाने पर, आज आपका मन कैसा है? (1 = बहुत मुश्किल, 5 = अच्छा)",
    "क्या कोई ऐसी चीज़ है जिसमें अभी आपको मदद चाहिए?",
    "क्या आप घर पर और आस-पास सुरक्षित महसूस कर रही हैं?",
    "आज कोई और बात जो आप मुझसे साझा करना चाहेंगी?",
  ],
};

export const ACKNOWLEDGEMENTS = {
  positive: {
    en: [
      "That's really good to hear 😊 It sounds like things are going a bit better.",
      "I'm glad you're doing okay. Thank you for sharing that with me.",
      "That's wonderful. Keep taking care of yourself.",
    ],
    hi: [
      "यह सुनकर अच्छा लगा 😊 लगता है थोड़ा बेहतर हो रहा है।",
      "खुशी है कि आप ठीक हैं। बताने के लिए धन्यवाद।",
      "बहुत अच्छा। अपना ख्याल रखते रहिए।",
    ],
  },
  neutral: {
    en: [
      "I hear you. Thank you for sharing that.",
      "Understood. Day-to-day things can feel heavy sometimes.",
      "I appreciate you telling me. We'll check in again soon.",
    ],
    hi: [
      "मैं समझती हूँ। बताने के लिए शुक्रिया।",
      "ठीक है। कभी-कभी दिन भारी लगते हैं।",
      "आपने बताया, इसके लिए शुक्रिया।",
    ],
  },
  negative: {
    en: [
      "I'm really sorry to hear that. You don't have to go through this alone.",
      "That sounds really hard. Please know that your assigned counsellor has been notified and will reach out soon.",
      "Thank you for trusting me with this. Help is on the way — you are not alone 💙",
    ],
    hi: [
      "यह सुनकर दुख हुआ। आपको अकेले नहीं झेलना है।",
      "यह बहुत मुश्किल लग रहा है। आपके काउंसलर को सूचित किया जा रहा है।",
      "मुझ पर भरोसा करने के लिए शुक्रिया। मदद आ रही है — आप अकेली नहीं हैं 💙",
    ],
  },
};

export const CLOSING_MESSAGES = {
  en: [
    "Thank you for trusting me and opening your heart today 🙏",
    "Your safety and healing matter deeply. Whenever you need someone to lean on, your Didi is always right here.",
    "Rest well, drink some water, and remember: you are so strong, and you are never alone. 💙",
  ],
  hi: [
    "आज अपनी दीदी से दिल की बात साझा करने के लिए बहुत प्यार 🙏",
    "तुमने बहुत हिम्मत दिखाई है। जब भी मन भारी हो या किसी की ज़रूरत हो, मैं हमेशा तुम्हारे लिए यहीं हूँ।",
    "अब थोड़ा आराम करो, थोड़ा पानी पियो, और याद रखना: तुम कभी अकेली नहीं हो। 💙",
  ],
};

export const LANGUAGE_LABELS = {
  en: 'English',
  hi: 'हिंदी',
};

export const pickRandom = (arr) => arr[Math.floor(Math.random() * arr.length)];
