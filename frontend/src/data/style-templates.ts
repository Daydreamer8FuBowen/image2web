export type StyleTemplate = {
  id: string
  name: string
  description: string
  prompt: string
  negativePrompt: string
  preview: string
}

const baseImageUrl = 'https://coresg-normal.trae.ai/api/ide/v1/text_to_image'

function makePreview(prompt: string) {
  return `${baseImageUrl}?prompt=${encodeURIComponent(prompt)}&image_size=landscape_4_3`
}

export const styleTemplates: StyleTemplate[] = [
  {
    id: 'product-polish',
    name: '产品精修',
    description: '适合主图净化、质感增强和商业背景统一。',
    prompt: '保留主体结构，清理杂物，统一高级电商背景，增强材质细节与反光质感',
    negativePrompt: '模糊，变形，低清晰度，多余物体，过曝',
    preview: makePreview('premium product photo on dark stone plinth with sharp specular highlights, luxury ecommerce style, realistic, studio lighting'),
  },
  {
    id: 'interior-shift',
    name: '室内换景',
    description: '替换背景材质和空间氛围，适合桌面、墙面、地板场景。',
    prompt: '把背景替换成高级室内空间，保留主体比例，加入柔和自然光和真实空间景深',
    negativePrompt: '透视错误，主体被遮挡，背景混乱，脏污',
    preview: makePreview('editorial interior redesign scene with warm wood walls and soft daylight, refined modern atmosphere, realistic render'),
  },
  {
    id: 'anime-redraw',
    name: '二次元重绘',
    description: '将实拍或草图转换为清爽动画风格。',
    prompt: '保留主体轮廓与动作，把画面重绘成高完成度二次元插画，线条干净，色彩统一',
    negativePrompt: '写实皮肤，杂乱线条，肢体错误，双重五官',
    preview: makePreview('anime illustration portrait with clean lineart, cinematic teal and coral palette, highly polished cel shading'),
  },
  {
    id: 'poster-drama',
    name: '海报增强',
    description: '强化戏剧光影与叙事氛围，适合活动海报与KV。',
    prompt: '增强海报感，加入戏剧化光影、视觉焦点和大片级层次，保留主体辨识度',
    negativePrompt: '平淡光线，构图松散，缺乏焦点，文字伪影',
    preview: makePreview('cinematic poster key visual with dramatic rim light, bold focal composition, premium campaign art direction'),
  },
  {
    id: 'material-swap',
    name: '材质替换',
    description: '快速把表面改为木纹、金属、玻璃或陶瓷。',
    prompt: '保留原始结构，把主体表面替换成精致材质，纹理真实，光线与反射自然',
    negativePrompt: '材质穿帮，表面拉伸，反射错误，脏污噪点',
    preview: makePreview('macro material study of brushed metal and smoked glass, realistic reflections, premium product visualization'),
  },
  {
    id: 'portrait-editorial',
    name: '人像风格化',
    description: '适合妆造升级、质感改写和时尚片风格转换。',
    prompt: '保留人物身份特征，提升妆造和服装层次，转换为高级时尚 editorial 风格',
    negativePrompt: '脸部变形，手部错误，皮肤塑料感，背景混乱',
    preview: makePreview('fashion editorial portrait with sculptural light, soft grain, rich blacks, luxurious styling, magazine photography'),
  },
]
