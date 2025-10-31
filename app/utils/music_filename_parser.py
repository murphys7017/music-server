"""
歌曲文件名规范化提取工具
支持从文件名和元数据中提取标准化的音乐信息
"""
import re
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# 常见的括号标记信息类型
BRACKET_INFO_PATTERNS = {
    'version': r'(国语版?|粤语版?|英文版?|日文版?|韩文版?|中文版?|翻唱版?|原版|demo版?|语言版|改编版|ver\.?|version)',
    'source': r'(电影|电视剧|动漫|游戏|原唱).*?(主题曲|片尾曲|插曲|ost)?',
    'type': r'(伴奏|纯音乐|live|acoustic|remix|cover|instrumental|inst\.?|edit|mix(?!.*\d))',
    'style': r'(说唱|摇滚|民谣|电子|爵士|古风|流行|吉他弹唱|女声|男声|甜味).*?(版|ver)?',
    'mix': r'(混音|重混|remix|remaster|mix\b)',
    'feat': r'(feat\.|featuring|ft\.|with)',
}

def extract_bracket_info(text: str) -> Dict[str, str]:
    """
    提取括号内的附加信息
    支持 ()、[]、<>、【】等括号
    """
    info = {
        'version': '',
        'source': '',
        'type': '',
        'style': '',
        'mix': '',
        'feat': '',
        'other': []
    }
    
    # 匹配所有括号内容
    bracket_pattern = r'[\(（\[<【]([^\)）\]>】]+)[\)）\]>】]'
    brackets = re.findall(bracket_pattern, text)
    
    for bracket_content in brackets:
        matched = False
        # 检查是否匹配已知模式
        for key, pattern in BRACKET_INFO_PATTERNS.items():
            if re.search(pattern, bracket_content, re.IGNORECASE):
                if not info[key]:  # 只保留第一个匹配
                    info[key] = bracket_content.strip()
                matched = True
                break
        
        # 未匹配的信息放入other
        if not matched:
            info['other'].append(bracket_content.strip())
    
    return info

def remove_brackets(text: str) -> str:
    """移除所有括号及其内容"""
    bracket_pattern = r'[\(（\[<【][^\)）\]>】]*[\)）\]>】]'
    return re.sub(bracket_pattern, '', text).strip()

def parse_filename(filename: str) -> Tuple[str, str]:
    """
    解析文件名，提取歌曲名和歌手
    格式: 歌曲名-歌手.ext 或 歌手-歌曲名.ext
    支持多艺术家（用 _ 或 & 分隔）
    """
    # 去除扩展名
    name_without_ext = Path(filename).stem
    
    # 分割歌曲名和歌手
    if ' - ' in name_without_ext:
        parts = name_without_ext.split(' - ', 1)
        song_part = parts[0].strip()
        artist_part = parts[1].strip()
        
        # 处理多艺术家：_ 替换为 ,
        if '_' in artist_part:
            artist_part = artist_part.replace('_', ', ')
        if ' & ' in artist_part:
            artist_part = artist_part.replace(' & ', ', ')
            
        return song_part, artist_part
    elif '-' in name_without_ext:
        parts = name_without_ext.split('-', 1)
        return parts[0].strip(), parts[1].strip()
    elif '_' in name_without_ext:
        parts = name_without_ext.split('_', 1)
        return parts[0].strip(), parts[1].strip()
    else:
        # 没有分隔符，全部作为歌曲名
        return name_without_ext.strip(), ''

def normalize_music_info(filename: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    综合文件名和元数据，提取标准化的音乐信息
    
    Args:
        filename: 文件名 (如: "夜曲(国语版)-周杰伦.mp3")
        metadata: 音频元数据字典 (可选，包含title, artist, album等)
    
    Returns:
        标准化的音乐信息字典
    """
    if metadata is None:
        metadata = {}
    
    # 解析文件名
    part1, part2 = parse_filename(filename)
    
    # 提取括号信息
    bracket_info_part1 = extract_bracket_info(part1)
    bracket_info_part2 = extract_bracket_info(part2)
    
    # 合并括号信息
    bracket_info = {}
    for k in bracket_info_part1.keys():
        if k == 'other':
            bracket_info[k] = list(bracket_info_part1['other']) + list(bracket_info_part2.get('other', []))
        else:
            bracket_info[k] = bracket_info_part1[k] or bracket_info_part2.get(k, '')
    
    # 移除括号后的纯净文本
    clean_part1 = remove_brackets(part1)
    clean_part2 = remove_brackets(part2)
    
    # 综合判断歌曲名和歌手
    # 优先使用元数据，其次使用文件名
    song_name = metadata.get('title') or metadata.get('name') or clean_part1
    artist = metadata.get('artist') or metadata.get('author') or clean_part2
    
    # 如果元数据中没有歌手但文件名有，可能是歌手-歌曲名格式
    if not artist and clean_part2 and not metadata.get('title'):
        # 尝试判断哪个更像歌手名（简单规则：较短的可能是歌手）
        if len(clean_part1) < len(clean_part2):
            artist = clean_part1
            song_name = clean_part2
    
    # 构建标准化信息
    normalized = {
        'name': song_name,
        'author': artist if artist else '未知',
        'album': metadata.get('album', ''),
        'version': bracket_info['version'],
        'source': bracket_info['source'],
        'type': bracket_info['type'],
        'style': bracket_info['style'],
        'mix': bracket_info['mix'],
        'feat': bracket_info['feat'],
        'extra_info': ' '.join(bracket_info['other']),
        'original_filename': filename,
    }
    
    # 如果是伴奏，标记类型
    if '伴奏' in filename or 'instrumental' in filename.lower() or 'inst.' in filename.lower() or 'inst_' in filename.lower():
        normalized['type'] = '伴奏'
    
    # 如果是live版本
    if 'live' in filename.lower():
        normalized['type'] = 'Live'
    
    # 如果是Remix
    if 'remix' in filename.lower() or 'mix)' in filename.lower():
        if not normalized['mix']:
            normalized['mix'] = 'Remix'
    
    return normalized

def generate_standard_filename(info: Dict[str, Any], include_extra: bool = False) -> str:
    """
    根据标准化信息生成规范的文件名
    
    Args:
        info: normalize_music_info返回的信息字典
        include_extra: 是否包含额外信息（版本、类型等）
    
    Returns:
        规范化的文件名（不含扩展名）
    """
    name = info['name']
    author = info['author']
    
    if include_extra:
        extras = []
        for key in ['version', 'type', 'source', 'style', 'mix']:
            if info.get(key):
                extras.append(info[key])
        
        if extras:
            extra_str = '(' + ','.join(extras) + ')'
            return f"{name}{extra_str}-{author}"
    
    return f"{name}-{author}"

# 示例用法
if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "玉盘 - 葫芦童声.mp3",
        "Libertus - Chen-U_EG.flac",
        "Silent Street (Type A) - Hyunmin Cho _ seibin _ Youngkyoung Choi _ SHIFT UP.mp3",
        "病名为爱 (国语) - 祖娅纳惜.mp3",
        "どうして… (为什么) - 凋叶棕.mp3",
        "BLUE DRAGON ('07 ver_) - 澤野弘之.mp3",
        "像鱼 (伴奏) - 王贰浪.mp3",
        "Let Her Go (DOAN Remix) - Doan.mp3",
        "The Edge (Original Mix) - Grant _ Nevve.mp3",
        "LEVEL5-judgelight- (instrumental) - fripSide.mp3",
        "Ghost (The Him Remix) - Au_Ra _ Alan Walker.mp3",
        "夢燈籠 (R7CKY 你的名字 Mix) - R7CKY.mp3",
        "病名为爱-古风版 (改编版原唱_ Neru) - 杨可爱.mp3",
        "RISE（中文版）登峰造极境（语言版） - 祈Inory.mp3",
        "My Dearest (Instrumental_TV Edit) - supercell.mp3",
        "All Alone With You (Inst_) - EGOIST.mp3",
        "答案 (女声吉他弹唱) - 李瑨瑶.mp3",
        "勾指起誓 (甜味小少年ver) - 洛少爷.mp3",
    ]
    
    for test in test_cases:
        result = normalize_music_info(test)
        print(f"\n原文件名: {test}")
        print(f"标准化结果:")
        print(f"  歌曲名: {result['name']}")
        print(f"  艺术家: {result['author']}")
        if result['version']:
            print(f"  版本: {result['version']}")
        if result['type']:
            print(f"  类型: {result['type']}")
        if result['style']:
            print(f"  风格: {result['style']}")
        if result['mix']:
            print(f"  混音: {result['mix']}")
        if result['extra_info']:
            print(f"  额外信息: {result['extra_info']}")
        print(f"  标准文件名: {generate_standard_filename(result)}")
