import sys
from pathlib import Path
# 在文件开头添加项目根目录到系统路径
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(BASE_DIR))

"""
图谱构建与社区摘要提示模板集合。

这些模板用于图谱索引的构建与维护流程。
"""

system_template_build_graph = """
-目标- 
你是一个专业的知识图谱构建助手。你的任务是根据给定的本体模型，从文本中精准提取实体和关系。

 -本体定义-
以下是系统中定义的实体类型及其含义，请严格理解这些定义：
{entity_types}
以下是允许的关系类型、含义及其约束（注意箭头方向）：
{relationship_types}
请注意区分定义的主体是实体类型和关系类型，我们所提供的类型虽然包括解释，但是提取时无需将解释包括其中，只需要提取关系类型即可！！！

-步骤- 
1.识别文本中的实体与关系，确保它们属于已定义实体类型与关系类型。对于每个已识别的实体和关系，提取以下信息： 
实体：
-entity_name：实体名称 
-entity_type：属于的实体类型,不属于已定义类型的实体不抽取
-entity_description：对实体属性和活动的综合描述
将每个实体格式化为("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

关系：
-source_entity：关系中源实体的名称， 
-target_entity：关系中目标实体的名称
-relationship_type：属于的关系类型，不属于已定义类型的关系不抽取
-relationship_description：解释为什么你认为源实体和目标实体是相互关联的 
-relationship_strength：一个数字评分，表示源实体和目标实体之间关系的强度 
将每个关系格式化为("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_type>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>) 

2.实体和关系的所有属性用中文输出，步骤1中识别的所有实体和关系输出为一个列表。使用**{record_delimiter}**作为列表分隔符。 
3.完成后，输出{completion_delimiter}

###################### 
-示例1- 

Entity_types: [电气设备, 故障类型, 故障表现, 故障原因,  抢修人员，抢修方法, 预防措施]
Relationship_types: [故障分类, 故障现象, 原因为, 分配维修, 需执行, 负责, 下一步, 可预防]
Text:
1.故障描述及原因简析：
断路器操作时拒分拒合，操作电源空开(或保险)和SF6 气压经运行人员检查属正常， 它可能的原因有操作机构机械异常、分合闸线圈异常、监控装置异常、通讯异常、直流系统电压异常等。
2.人员部署：
工作班成员由继保班和检修班组成，(如果怀疑开关本体绝缘及特性有问题，高试班参 加)。继保班两人，负责检查处理保护屏端子排以内范围故障，并负责整体工作安排协调； 检修班两人，负责检查处理保护屏端子排以外故障。################
Output:
("entity"{tuple_delimiter}"断路器"{tuple_delimiter}"电气设备"{tuple_delimiter}"主要电气设备，操作时出现拒分拒合故障"){record_delimiter}
("entity"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"故障表现"{tuple_delimiter}"断路器操动机构故障的故障表现，即拒绝分闸和合闸"){record_delimiter}
("entity"{tuple_delimiter}"操作机构机械异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"){record_delimiter}
("entity"{tuple_delimiter}"分合闸线圈异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"){record_delimiter}
("entity"{tuple_delimiter}"监控装置异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"){record_delimiter}
("entity"{tuple_delimiter}"通讯异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"{tuple_delimiter}7){record_delimiter}
("entity"{tuple_delimiter}"直流系统电压异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"{tuple_delimiter}6){record_delimiter}
("entity"{tuple_delimiter}"监控装置异常"{tuple_delimiter}"故障原因"{tuple_delimiter}"可能导致断路器拒分拒合的原因之一"){record_delimiter}
("entity"{tuple_delimiter}"继保班"{tuple_delimiter}"抢修人员"{tuple_delimiter}"负责检查处理保护屏端子排以内范围故障并负责整体工作安排协调的团队"){record_delimiter}
("entity"{tuple_delimiter}"检修班"{tuple_delimiter}"抢修人员"{tuple_delimiter}"负责检查处理保护屏端子排以外故障的团队"){record_delimiter}
("entity"{tuple_delimiter}"高试班"{tuple_delimiter}"抢修人员"{tuple_delimiter}"如果怀疑开关本体绝缘及特性有问题，则参加的团队"){record_delimiter}
("entity"{tuple_delimiter}"检查处理保护屏端子排以内范围故障"{tuple_delimiter}"处置方法"{tuple_delimiter}"继保班负责的处置方法，检查和处理保护屏端子排以内的故障"){record_delimiter}
("entity"{tuple_delimiter}"整体工作安排协调"{tuple_delimiter}"处置方法"{tuple_delimiter}"继保班负责的处置方法，进行整体工作安排和协调"){record_delimiter}
("entity"{tuple_delimiter}"检查处理保护屏端子排以外故障"{tuple_delimiter}"处置方法"{tuple_delimiter}"检修班负责的处置方法，检查和处理保护屏端子排以外的故障"){record_delimiter}
("relationship"{tuple_delimiter}"断路器"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"故障现象"{tuple_delimiter}"拒分拒合是断路器的故障表现（文中无故障类型，因此对应电气设备-断路器。由于是示例特此说明，你执行时无需说明）"{tuple_delimiter}9){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"操作机构机械异常"{tuple_delimiter}"原因为"{tuple_delimiter}"拒分拒合故障的原因可能是操作机构机械异常"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"分合闸线圈异常"{tuple_delimiter}"原因为"{tuple_delimiter}"拒分拒合故障的原因可能是分合闸线圈异常"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"监控装置异常"{tuple_delimiter}"原因为"{tuple_delimiter}"拒分拒合故障的原因可能是监控装置异常"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"通讯异常"{tuple_delimiter}"原因为"{tuple_delimiter}"拒分拒合故障的原因可能是通讯异常"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"直流系统电压异常"{tuple_delimiter}"原因为"{tuple_delimiter}"拒分拒合故障的原因可能是直流系统电压异常"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"继保班"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"分配维修"{tuple_delimiter}"继保班被分配维修断路器拒分拒合"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"高试班"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"分配维修"{tuple_delimiter}"高试班被分配维修断路器拒分拒合"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"检修班"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"分配维修"{tuple_delimiter}"检修班被分配维修断路器拒分拒合"{tuple_delimiter}10){completion_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"检查处理保护屏端子排以内范围故障"{tuple_delimiter}"需执行"{tuple_delimiter}"抢修断路器拒分拒合需执行检查处理保护屏端子排以内范围故障"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"拒分拒合"{tuple_delimiter}"检查处理保护屏端子排以外故障"{tuple_delimiter}"需执行"{tuple_delimiter}"抢修断路器拒分拒合需执行检查处理保护屏端子排以外故障"{tuple_delimiter}8){record_delimiter}
("relationship"{tuple_delimiter}"继保班"{tuple_delimiter}"检查处理保护屏端子排以内范围故障"{tuple_delimiter}"负责"{tuple_delimiter}"继保班被分配负责检查处理保护屏端子排以内范围故障"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"继保班"{tuple_delimiter}"整体工作安排协调"{tuple_delimiter}"负责"{tuple_delimiter}"继保班被分配负责整体工作安排协调"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"检修班"{tuple_delimiter}"检查处理保护屏端子排以外故障"{tuple_delimiter}"负责"{tuple_delimiter}"检修班被分配负责检查处理保护屏端子排以外故障"{tuple_delimiter}10){completion_delimiter}#############################
#############################
-示例2-

Entity_types: [电气设备, 故障类型, 故障表现, 故障原因,  抢修人员，抢修方法, 预防措施]
Relationship_types: [故障分类, 故障现象, 原因为, 分配维修, 需执行, 负责, 下一步, 可预防]
Text:
#############################

-规则-
1. 禁止输出 JSON、Markdown、列表或任何其他特殊格式。
2. 必须使用格式：("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)
3. 必须使用格式：("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_type>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)
4. 实体描述不能为空，必须根据上下文总结实体的属性或行为。
5.可能会出现某些实体类型和关系类型未出现，这种情况是正常的。
6.某些关系类型的对应有优先，例如故障现象优先描述故障类型对应故障表现，无故障类型则描述电气设备对应故障表现。
"""

human_template_build_graph = """
-真实数据- 
###################### 
实体类型：{entity_types}
关系类型：{relationship_types}
文本：{input_text} 
（请注意，真实数据中所提供的实体类型和关系类型虽然包括解释，但是提取时无需将解释包括其中！！！）
###################### 
输出：
"""

system_template_build_index = """
你是一名数据处理助理。您的任务是识别列表中的重复实体，并决定应合并哪些实体。 
这些实体在格式或内容上可能略有不同，但本质上指的是同一个实体。运用你的分析技能来确定重复的实体。 
以下是识别重复实体的规则：
1.类型一致性原则（至关重要）：只有当两个实体属于同一个“实体类型”（即方括号内的类型相同）时，才能合并。
   - 例如："变压器 [设备]" 和 "1#变压器 [设备]" -> 可以合并。
   - 例如："变压器 [设备]" 和 "变压器故障 [故障表现]" -> **禁止合并**。
2.语义上差异较小的实体应被视为重复。 
3.格式不同但内容相同的实体应被视为重复。 
4.引用同一现实世界对象或概念的实体，即使描述不同，也应被视为重复。 
5.如果它指的是不同的数字、日期或产品型号，请不要合并实体。
输出格式：
1.将要合并的实体输出为Python列表的格式，输出时保持它们输入时的原文。
2.如果有多组可以合并的实体，每组输出为一个单独的列表，每组分开输出为一行。
3.如果没有要合并的实体，就输出一个空的列表。
4.只输出列表即可，不需要其它的说明。
5.不要输出嵌套的列表，只输出列表。
###################### 
-示例- 
###################### 
Example 1:
Example 1:
Input: ['Star Ocean The Second Story R [Game]', 'Star Ocean: The Second Story R [Game]', 'Star Ocean: A Research Journey [Book]']
Output:
['Star Ocean The Second Story R', 'Star Ocean: The Second Story R']

Example 2 (类型冲突示例):
Input: ['变压器 [电气设备]', '变压器油温过高 [故障表现]']
Output:
[]

Example 3:
Input: ['Sony [Company]', 'Sony Inc [Company]', 'Google [Company]']
Output:
['Sony', 'Sony Inc']
#############################
"""

user_template_build_index = """
以下是要处理的实体列表： 
{entities} 
请识别重复的实体，提供可以合并的实体列表。
输出：
"""

community_template = """
基于所提供的属于同一图社区的节点和关系， 
生成所提供图社区信息的自然语言摘要： 
{community_info} 
摘要：
"""

COMMUNITY_SUMMARY_PROMPT = """
给定一个输入三元组，生成信息摘要。没有序言。
"""

entity_alignment_prompt = """
Given these entities that should refer to the same concept:
{entity_desc}

Which entity ID best represents the canonical form? Reply with only the entity ID."""

__all__ = [
    "system_template_build_graph",
    "human_template_build_graph",
    "system_template_build_index",
    "user_template_build_index",
    "community_template",
    "COMMUNITY_SUMMARY_PROMPT",
    "entity_alignment_prompt",
]
