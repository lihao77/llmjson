#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱数据验证器

提供知识图谱数据的验证和修正功能。"""

import re
import json
import ast
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime
from .exceptions import ValidationError


class DataValidator:
    """知识图谱数据验证器"""
    
    def __init__(self):
        """初始化数据验证器"""
        # 初始化验证报告
        self.reset_validation_report()
        # 定义ID格式的正则表达式
        self.id_patterns = {
            # 事件ID: E-<行政区划码>[>乡镇街道等子区域]-<日期YYYYMMDD>-<事件类型>
            "event": re.compile(r'^E-([A-Za-z0-9]+)(>[^-]+)?-([0-9]{8})-([A-Z_]+)$'),
            # 地点ID: L-<行政区划码>[>乡镇街道等子区域] 或 L-<实体类型>-<名称>[>区段]
            "location": re.compile(r'^L-([A-Za-z0-9]+)(>[^-]+)?$|^L-([A-Z_]+)-([^>]+)(>[^-]+)?$'),
            # 设施ID: F-<行政区划码>[>乡镇街道等子区域]-<设施名称>
            "facility": re.compile(r'^F-([A-Za-z0-9]+)(>[^-]+)?-(.+)$'),
            # 事件状态ID: ES-<事件ID>-<开始日期YYYYMMDD>_<结束日期YYYYMMDD>
            "event_state": re.compile(r'^ES-E-([A-Za-z0-9]+)(>[^-]+)?-([0-9]{8})-([A-Z_]+)-([0-9]{8})_([0-9]{8})$'),
            # 地点状态ID: LS-<地点ID>-<开始日期YYYYMMDD>_<结束日期YYYYMMDD>
            "location_state": re.compile(r'^LS-L-([A-Za-z0-9]+)(>[^-]+)?-([0-9]{8})_([0-9]{8})$|^LS-L-([A-Z_]+)-([^>-]+)(>[^-]+)?-([0-9]{8})_([0-9]{8})$'),
            # 设施状态ID: FS-<设施ID>-<开始日期YYYYMMDD>_<结束日期YYYYMMDD>
            "facility_state": re.compile(r'^FS-F-([A-Za-z0-9]+)(>[^-]+)?-(.+)-([0-9]{8})_([0-9]{8})$'),
            # 联合状态ID: JS-<关联的基础实体ID列表>-<开始日期YYYYMMDD>_<结束日期YYYYMMDD>
            "joint_state": re.compile(r'^JS-(.+)-([0-9]{8})_([0-9]{8})$')
        }
        # 允许的关系类型
        self.allowed_relations = ["触发", "影响", "调控", "导致", "隐含导致"]
        # 允许的状态类型
        self.allowed_state_types = ["独立状态", "联合状态"]
        # 时间格式正则表达式
        self.time_pattern = re.compile(r'^([0-9]{4})-([0-9]{2})-([0-9]{2})至([0-9]{4})-([0-9]{2})-([0-9]{2})$')
    
    def reset_validation_report(self):
        """重置验证报告"""
        self.validation_report = {
            "errors_deleted": [],  # 删除的错误
            "warnings_modified": [],  # 修改的警告
            "warnings_unmodified": [],  # 未修改的警告
            "corrections": [],  # 修正记录
            "error_stats": {
                "base_entities": set(),  # 记录出错的基础实体ID
                "state_entities": set(),  # 记录出错的状态实体ID
                "state_relations": set()  # 记录出错的状态关系ID
            },
            "error_counts": {
                "base_entities": 0,
                "state_entities": 0,
                "state_relations": 0,
                "total": 0
            },
            "error_rates": {
                "base_entities": 0.0,
                "state_entities": 0.0,
                "state_relations": 0.0,
                "total": 0.0
            }
        }
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取完整的验证报告"""
        # 将set数据类型转化为list返回
        self.validation_report["error_stats"] = {
            "base_entities": list(self.validation_report["error_stats"]["base_entities"]),
            "state_entities": list(self.validation_report["error_stats"]["state_entities"]),
            "state_relations": list(self.validation_report["error_stats"]["state_relations"])
        }
        return self.validation_report
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证摘要信息
        
        Returns:
            验证摘要，包含错误数量、警告数量、修正数量等关键信息
        """
        return {
            "error_count": self.validation_report["error_counts"]["total"],
            "warning_count": len(self.validation_report["warnings_unmodified"]),
            "correction_count": len(self.validation_report["warnings_modified"]),
            "error_rate": self.validation_report["error_rates"]["total"],
            "success_rate": 1.0 - self.validation_report["error_rates"]["total"],
            "base_entity_errors": self.validation_report["error_counts"]["base_entities"],
            "state_entity_errors": self.validation_report["error_counts"]["state_entities"],
            "state_relation_errors": self.validation_report["error_counts"]["state_relations"],
            "total_items_processed": (
                self.validation_report.get('total_entities', 0) +
                self.validation_report.get('total_states', 0) +
                self.validation_report.get('total_relations', 0)
            )
        }
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """验证并修正知识图谱数据

        Args:
            data: 知识图谱数据，包含基础实体、状态实体和状态关系

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (修正后的知识图谱数据, 验证报告)
        """
        # 重置验证报告
        self.reset_validation_report()

        # 深拷贝数据，避免修改原始数据
        validated_data = {
            "基础实体": data.get("基础实体", []).copy(),
            "状态实体": data.get("状态实体", []).copy(),
            "状态关系": data.get("状态关系", []).copy()
        }

        # 第一步：验证基础实体ID格式
        validated_data["基础实体"] = self._validate_base_entities(validated_data["基础实体"])

        # 第二步：验证状态实体
        validated_data["状态实体"], validated_data["状态关系"] = self._validate_state_entities(
            validated_data["状态实体"], validated_data["基础实体"], validated_data["状态关系"]
        )

        # 第三步：验证状态关系
        validated_data["状态关系"] = self._validate_state_relations(
            validated_data["状态关系"], validated_data["状态实体"]
        )

        # 计算错误数量统计
        base_entity_count = len(data.get("基础实体", []))
        state_entity_count = len(data.get("状态实体", []))
        state_relation_count = len(data.get("状态关系", []))
        total_entities = base_entity_count + state_entity_count + state_relation_count
        
        base_entity_error_count = len(self.validation_report["error_stats"]["base_entities"])
        state_entity_error_count = len(self.validation_report["error_stats"]["state_entities"])
        state_relation_error_count = len(self.validation_report["error_stats"]["state_relations"])
        total_error_count = base_entity_error_count + state_entity_error_count + state_relation_error_count
        
        # 更新错误数量统计
        self.validation_report["error_counts"]["base_entities"] = base_entity_error_count
        self.validation_report["error_counts"]["state_entities"] = state_entity_error_count
        self.validation_report["error_counts"]["state_relations"] = state_relation_error_count
        self.validation_report["error_counts"]["total"] = total_error_count
        
        # 计算错误率统计
        self.validation_report["error_rates"]["base_entities"] = base_entity_error_count / base_entity_count if base_entity_count > 0 else 0.0
        self.validation_report["error_rates"]["state_entities"] = state_entity_error_count / state_entity_count if state_entity_count > 0 else 0.0
        self.validation_report["error_rates"]["state_relations"] = state_relation_error_count / state_relation_count if state_relation_count > 0 else 0.0
        self.validation_report["error_rates"]["total"] = total_error_count / total_entities if total_entities > 0 else 0.0
        
        # 保持向后兼容
        self.validation_report["error_rate"] = self.validation_report["error_rates"]["total"]
        self.validation_report['total_entities'] = base_entity_count
        self.validation_report['total_states'] = state_entity_count
        self.validation_report['total_relations'] = state_relation_count
        

        return validated_data, self.get_validation_report()
    
    def _validate_base_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证基础实体

        Args:
            entities: 基础实体列表

        Returns:
            验证后的基础实体列表
        """
        valid_entities = []
        entity_ids = set()  # 用于检测重复ID

        for entity in entities:
            entity_type = entity.get("类型")
            entity_id = entity.get("唯一ID")

            # 检查必要字段
            if not entity_type or not entity_id:
                self.validation_report["errors_deleted"].append(f"实体缺少必要字段：{entity}")
                if entity_id:
                    self.validation_report["error_stats"]["base_entities"].add(entity_id)
                continue

            # 检查ID格式
            is_valid_id = False
            if entity_type == "事件":
                is_valid_id = bool(self.id_patterns["event"].match(entity_id))
            elif entity_type == "地点":
                is_valid_id = bool(self.id_patterns["location"].match(entity_id))
            elif entity_type == "设施":
                is_valid_id = bool(self.id_patterns["facility"].match(entity_id))

            if not is_valid_id:
                self.validation_report["errors_deleted"].append(f"实体ID格式错误：{entity_id}")
                self.validation_report["error_stats"]["base_entities"].add(entity_id)
                continue

            # 检查地点和设施是否有地理描述
            if entity_type in ["地点", "设施"] and not entity.get("地理描述"):
                self.validation_report["warnings_unmodified"].append(f"实体缺少地理描述：{entity_id}")
                self.validation_report["error_stats"]["base_entities"].add(entity_id)

            # 检查ID是否重复
            if entity_id in entity_ids:
                self.validation_report["warnings_unmodified"].append(f"发现重复的实体ID：{entity_id}")
                self.validation_report["error_stats"]["base_entities"].add(entity_id)
            else:
                entity_ids.add(entity_id)
                valid_entities.append(entity)

        return valid_entities

    def _validate_state_entities(self, states: List[Dict[str, Any]], base_entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
        """验证状态实体

        Args:
            states: 状态实体列表
            base_entities: 基础实体列表

        Returns:
            验证后的状态实体列表
        """
        valid_states = []
        # print(type(relations))
        valid_relations = relations.copy()
        base_entity_ids = {entity["唯一ID"] for entity in base_entities}  # 所有有效的基础实体ID
        id_mapping = {}  # 用于记录ID修改映射

        for state in states:
            state_type = state.get("类型")
            state_id = state.get("状态ID")
            entity_ids = state.get("关联实体ID列表", [])
            time_range = state.get("时间")
            original_state_id = state_id

            # 检查必要字段
            if not state_type or not state_id or not entity_ids or not time_range:
                self.validation_report["errors_deleted"].append(f"状态实体缺少必要字段：{state}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)
                continue

            # 检查状态类型
            if state_type not in self.allowed_state_types:
                self.validation_report["errors_deleted"].append(f"状态类型错误：{state_type}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)
                continue

            # 检查时间格式
            if not self.time_pattern.match(time_range):
                # 尝试修正时间格式
                corrected_time = self._correct_time_format(time_range)
                if corrected_time:
                    self.validation_report["warnings_modified"].append(f"已修正时间格式：{time_range} -> {corrected_time}")
                    state["时间"] = corrected_time
                else:
                    self.validation_report["warnings_unmodified"].append(f"时间格式错误：{time_range}")
                    self.validation_report["error_stats"]["state_entities"].add(state_id)

            # 原则3：去除状态实体关联实体ID列表中的重复ID
            if len(entity_ids) != len(set(entity_ids)):
                if type(entity_ids) == str:
                    # 尝试转换为列表,ai的结构化输出能力太弱了
                    entity_ids = ast.literal_eval(entity_ids)
                original_ids = entity_ids.copy()
                entity_ids = list(dict.fromkeys(entity_ids))  # 保持顺序去重
                state["关联实体ID列表"] = entity_ids
                self.validation_report["warnings_modified"].append(f"已去除重复的关联实体ID：{original_ids} -> {entity_ids}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)

            # 检查联合状态是否至少关联两个实体
            if state_type == "联合状态" and len(entity_ids) < 2:
                
                # 自动转换为独立状态并更新ID前缀
                state["类型"] = "独立状态"
                entity_id = entity_ids[0]
                if entity_id.startswith("E-"):
                    new_prefix = "ES"
                elif entity_id.startswith("L-"):
                    new_prefix = "LS"
                elif entity_id.startswith("F-"):
                    new_prefix = "FS"
                time_part = "-".join(state_id.split("-")[-1:])
                new_state_id = f"{new_prefix}-{entity_id}-{time_part}"
                state["状态ID"] = new_state_id
                id_mapping[original_state_id] = new_state_id
                self.validation_report["warnings_modified"].append(f"联合状态转换为独立状态并更新ID：{state_id} -> {state['状态ID']}")
                self.validation_report["error_stats"]["state_entities"].add(new_state_id)

            # 检查独立状态是否只关联一个实体
            if state_type == "独立状态" and len(entity_ids) > 1:
                
                # 自动转换为联合状态并更新ID前缀
                state["类型"] = "联合状态"
                entity_part = "-".join(sorted(entity_ids))
                time_part = "-".join(state_id.split("-")[-1:])
                new_state_id = f"JS-{entity_part}-{time_part}"
                state["状态ID"] = new_state_id
                id_mapping[original_state_id] = new_state_id
                self.validation_report["warnings_modified"].append(f"独立状态转换为联合状态并更新ID：{state_id} -> {state['状态ID']}")
                self.validation_report["error_stats"]["state_entities"].add(new_state_id)

            # 检查关联实体是否存在
            invalid_entity_ids = [eid for eid in entity_ids if eid not in base_entity_ids]
            if invalid_entity_ids:
                self.validation_report["errors_deleted"].append(f"关联不存在的实体ID：{invalid_entity_ids}")
                continue

            # 原则6：对于联合状态，按关联ID名称排序重新生成ID
            if state_type == "联合状态":
                # 排序关联实体ID
                sorted_entity_ids = sorted(entity_ids)
                if sorted_entity_ids != entity_ids:
                    
                    # 提取时间部分
                    time_part = "-".join(state_id.split("-")[-1:])  # 获取最后一部分（日期范围）
                    # 生成新的状态ID
                    new_state_id = f"JS-{'-'.join(sorted_entity_ids)}-{time_part}"
                    state["关联实体ID列表"] = sorted_entity_ids
                    state["状态ID"] = new_state_id
                    id_mapping[original_state_id] = new_state_id
                    self.validation_report["warnings_modified"].append(f"已重新排序联合状态ID：{original_state_id} -> {new_state_id}")

            # 原则2：检查状态ID与关联实体ID列表的一致性
            is_valid_state_id = self._validate_state_id(state["状态ID"], state["类型"], state["关联实体ID列表"], state["时间"])
            if not is_valid_state_id:
                # 尝试修正状态ID
                
                corrected_state_id = self._generate_correct_state_id(state["类型"], state["关联实体ID列表"], state["时间"])
                if corrected_state_id:
                    state["状态ID"] = corrected_state_id
                    id_mapping[original_state_id] = corrected_state_id
                    self.validation_report["warnings_modified"].append(f"已修正状态ID：{original_state_id} -> {corrected_state_id}")
                    state_id = corrected_state_id

                else:
                    self.validation_report["warnings_unmodified"].append(f"状态ID格式错误且无法修正：{state_id}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)

            # 检查ID是否重复
            # if state_id in state_ids:
            #     self.validation_report["warnings_unmodified"].append(f"发现重复的状态ID：{state_id}")
            # else:
            #     state_ids.add(state_id)
            #     valid_states.append(state)
            valid_states.append(state)
        # 原则4：更新所有状态关系中的ID引用
        if id_mapping:
            valid_relations = self._update_state_relation_references(valid_relations, id_mapping)
        return valid_states, valid_relations

    def _validate_state_relations(self, relations: List[Dict[str, Any]], states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证状态关系

        Args:
            relations: 状态关系列表
            states: 状态实体列表

        Returns:
            验证后的状态关系列表
        """
        valid_relations = []
        state_ids = {state["状态ID"] for state in states}  # 所有有效的状态ID

        for relation in relations:
            subject_id = relation.get("主体状态ID")
            relation_type = relation.get("关系")
            object_id = relation.get("客体状态ID")
            basis = relation.get("依据")

            # 检查必要字段
            if not subject_id or not relation_type or not object_id:
                self.validation_report["errors_deleted"].append(f"状态关系缺少必要字段：{relation}")
                if subject_id:
                    self.validation_report["error_stats"]["state_relations"].add(subject_id)
                if object_id:
                    self.validation_report["error_stats"]["state_relations"].add(object_id)
                continue

            # 检查关系类型
            if relation_type not in self.allowed_relations:
                self.validation_report["warnings_unmodified"].append(f"关系类型不在允许列表中：{relation_type}")
                self.validation_report["error_stats"]["state_relations"].add(subject_id)
                self.validation_report["error_stats"]["state_relations"].add(object_id)

            # 检查依据是否为空
            if not basis:
                self.validation_report["warnings_unmodified"].append(f"状态关系缺少依据：{relation}")
                self.validation_report["error_stats"]["state_relations"].add(subject_id)
                self.validation_report["error_stats"]["state_relations"].add(object_id)

            # 原则5：检查引用的状态ID是否存在
            if subject_id not in state_ids:
                self.validation_report["errors_deleted"].append(f"引用不存在的主体状态ID：{subject_id}")
                self.validation_report["error_stats"]["state_relations"].add(subject_id)
                continue

            if object_id not in state_ids:
                self.validation_report["errors_deleted"].append(f"引用不存在的客体状态ID：{object_id}")
                self.validation_report["error_stats"]["state_relations"].add(object_id)
                continue

            valid_relations.append(relation)

        return valid_relations

    def _validate_state_id(self, state_id: str, state_type: str, entity_ids: List[str], time_range: str) -> bool:
        """验证状态ID与关联实体ID列表的一致性

        Args:
            state_id: 状态ID
            state_type: 状态类型
            entity_ids: 关联实体ID列表
            time_range: 时间范围

        Returns:
            状态ID是否有效
        """
        # 从时间范围中提取日期
        time_match = self.time_pattern.match(time_range)
        if not time_match:
            return False

        start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
        end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
        date_part = f"{start_date}_{end_date}"

        # 检查状态ID格式
        if state_type == "独立状态":
            # 独立状态只关联一个实体
            entity_id = entity_ids[0]
            if entity_id.startswith("E-"):
                # 事件状态
                expected_prefix = f"ES-{entity_id}-{date_part}"
                return state_id == expected_prefix
            elif entity_id.startswith("L-"):
                # 地点状态
                expected_prefix = f"LS-{entity_id}-{date_part}"
                return state_id == expected_prefix
            elif entity_id.startswith("F-"):
                # 设施状态
                expected_prefix = f"FS-{entity_id}-{date_part}"
                return state_id == expected_prefix
        elif state_type == "联合状态":
            # 联合状态关联多个实体
            # 检查ID中是否包含所有关联实体ID
            entity_part = "-".join(sorted(entity_ids))
            expected_id = f"JS-{entity_part}-{date_part}"
            return state_id == expected_id

        return False

    def _generate_correct_state_id(self, state_type: str, entity_ids: List[str], time_range: str) -> Optional[str]:
        """生成正确的状态ID

        Args:
            state_type: 状态类型
            entity_ids: 关联实体ID列表
            time_range: 时间范围

        Returns:
            正确的状态ID，如果无法生成则返回None
        """
        # 从时间范围中提取日期
        time_match = self.time_pattern.match(time_range)
        if not time_match:
            return None

        start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
        end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
        date_part = f"{start_date}_{end_date}"

        if state_type == "独立状态" and len(entity_ids) == 1:
            # 独立状态只关联一个实体
            entity_id = entity_ids[0]
            if entity_id.startswith("E-"):
                # 事件状态
                return f"ES-{entity_id}-{date_part}"
            elif entity_id.startswith("L-"):
                # 地点状态
                return f"LS-{entity_id}-{date_part}"
            elif entity_id.startswith("F-"):
                # 设施状态
                return f"FS-{entity_id}-{date_part}"
        elif state_type == "联合状态" and len(entity_ids) >= 2:
            # 联合状态关联多个实体
            entity_part = "-".join(sorted(entity_ids))
            return f"JS-{entity_part}-{date_part}"

        return None

    def _update_state_relation_references(self, relations: List[Dict[str, Any]], id_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """更新状态关系中的ID引用

        Args:
            relations: 状态关系列表
            id_mapping: ID映射字典，键为原ID，值为新ID

        Returns:
            更新后的状态关系列表
        """
        for relation in relations:
            # 更新主体状态ID
            subject_id = relation.get("主体状态ID")
            if subject_id in id_mapping:
                relation["主体状态ID"] = id_mapping[subject_id]
                # self.validation_report["warnings_modified"].append(f"已更新状态关系的主体状态ID：{subject_id} -> {id_mapping[subject_id]}")
            
            # 更新客体状态ID
            object_id = relation.get("客体状态ID")
            if object_id in id_mapping:
                relation["客体状态ID"] = id_mapping[object_id]
                # self.validation_report["warnings_modified"].append(f"已更新状态关系的客体状态ID：{object_id} -> {id_mapping[object_id]}")
        # print("状态关系ID更新完成")
        return relations

    def _correct_time_format(self, time_str: str) -> Optional[str]:
        """尝试修正时间格式

        Args:
            time_str: 时间字符串

        Returns:
            修正后的时间字符串，如果无法修正则返回None
        """
        # 尝试修正常见的时间格式错误
        # 例如：将"2023-10-01到2023-10-10"修正为"2023-10-01至2023-10-10"
        if "到" in time_str:
            return time_str.replace("到", "至")
        
        # 可以添加更多的时间格式修正规则
        
        return None

    def _calculate_success_rate(self) -> float:
        """计算验证成功率"""
        total_items = (
            self.validation_report.get('total_entities', 0) +
            self.validation_report.get('total_states', 0) +
            self.validation_report.get('total_relations', 0)
        )
        
        if total_items == 0:
            return 1.0
        
        error_count = len(self.validation_report.get('errors_deleted', []))
        return max(0.0, (total_items - error_count) / total_items)
    
    def export_validation_report(self, file_path: str):
        """导出验证报告到文件
        
        Args:
            file_path: 导出文件路径
        """
        report_data = {
            'details': self.get_validation_report(),
            'summary': self.get_validation_summary(),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            

class DataValidator_1(DataValidator):

    def _validate_state_entities(self, states: List[Dict[str, Any]], base_entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """验证状态实体，支持状态ID区分码唯一性处理"""
        valid_states = []
        valid_relations = relations.copy()
        base_entity_ids = {entity["唯一ID"] for entity in base_entities}
        id_mapping = {}
        # 用于检测同一实体+时间段下的状态ID冲突
        state_id_counter = {}
        # key: (类型, tuple(关联实体ID), 时间), value: [state索引列表]
        state_group = {}
        # 先按实体+时间分组
        for idx, state in enumerate(states):
            state_type = state.get("类型")
            entity_ids = state.get("关联实体ID列表", [])
            time_range = state.get("时间")
            # 规范化entity_ids
            if isinstance(entity_ids, str):
                try:
                    entity_ids = ast.literal_eval(entity_ids)
                except Exception:
                    entity_ids = [entity_ids]
            entity_ids_tuple = tuple(sorted(entity_ids))
            key = (state_type, entity_ids_tuple, time_range)
            state_group.setdefault(key, []).append(idx)

        # 统计同组数量，决定是否加区分码
        group_need_code = {k: len(v) > 1 for k, v in state_group.items()}

        # 记录每组已分配的区分码
        group_code_count = {k: 1 for k, v in state_group.items() if group_need_code[k]}

        for idx, state in enumerate(states):
            state_type = state.get("类型")
            state_id = state.get("状态ID")
            entity_ids = state.get("关联实体ID列表", [])
            time_range = state.get("时间")
            original_state_id = state_id

            # 检查必要字段
            if not state_type or not state_id or not entity_ids or not time_range:
                self.validation_report["errors_deleted"].append(f"状态实体缺少必要字段：{state}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)
                continue

            # 检查状态类型
            if state_type not in self.allowed_state_types:
                self.validation_report["errors_deleted"].append(f"状态类型错误：{state_type}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)
                continue

            # 检查时间格式
            if not self.time_pattern.match(time_range):
                corrected_time = self._correct_time_format(time_range)
                if corrected_time:
                    self.validation_report["warnings_modified"].append(f"已修正时间格式：{time_range} -> {corrected_time}")
                    state["时间"] = corrected_time
                else:
                    self.validation_report["warnings_unmodified"].append(f"时间格式错误：{time_range}")
                    self.validation_report["error_stats"]["state_entities"].add(state_id)

            # 去重
            if len(entity_ids) != len(set(entity_ids)):
                if isinstance(entity_ids, str):
                    entity_ids = ast.literal_eval(entity_ids)
                original_ids = entity_ids.copy()
                entity_ids = list(dict.fromkeys(entity_ids))
                state["关联实体ID列表"] = entity_ids
                self.validation_report["warnings_modified"].append(f"已去除重复的关联实体ID：{original_ids} -> {entity_ids}")
                self.validation_report["error_stats"]["state_entities"].add(state_id)

            # 检查联合/独立状态实体数量
            if state_type == "联合状态" and len(entity_ids) < 2:
                state["类型"] = "独立状态"
                entity_id = entity_ids[0]
                if entity_id.startswith("E-"):
                    new_prefix = "ES"
                elif entity_id.startswith("L-"):
                    new_prefix = "LS"
                elif entity_id.startswith("F-"):
                    new_prefix = "FS"
                else:
                    new_prefix = "ES"
                # 时间部分
                time_match = self.time_pattern.match(state["时间"])
                if time_match:
                    start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
                    end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
                    date_part = f"{start_date}_{end_date}"
                    new_state_id = f"{new_prefix}-{entity_id}-{date_part}"
                    state["状态ID"] = new_state_id
                    id_mapping[original_state_id] = new_state_id
                    self.validation_report["warnings_modified"].append(f"联合状态转换为独立状态并更新ID：{state_id} -> {state['状态ID']}")
                    self.validation_report["error_stats"]["state_entities"].add(new_state_id)

            if state_type == "独立状态" and len(entity_ids) > 1:
                state["类型"] = "联合状态"
                entity_part = "-".join(sorted(entity_ids))
                time_match = self.time_pattern.match(state["时间"])
                if time_match:
                    start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
                    end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
                    date_part = f"{start_date}_{end_date}"
                    new_state_id = f"JS-{entity_part}-{date_part}"
                    state["状态ID"] = new_state_id
                    id_mapping[original_state_id] = new_state_id
                    self.validation_report["warnings_modified"].append(f"独立状态转换为联合状态并更新ID：{state_id} -> {state['状态ID']}")
                    self.validation_report["error_stats"]["state_entities"].add(new_state_id)

            # 检查实体是否存在
            invalid_entity_ids = [eid for eid in entity_ids if eid not in base_entity_ids]
            if invalid_entity_ids:
                self.validation_report["errors_deleted"].append(f"关联不存在的实体ID：{invalid_entity_ids}")
                continue

            # 联合状态排序
            if state_type == "联合状态":
                sorted_entity_ids = sorted(entity_ids)
                if sorted_entity_ids != entity_ids:
                    time_match = self.time_pattern.match(state["时间"])
                    if time_match:
                        start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
                        end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
                        date_part = f"{start_date}_{end_date}"
                        new_state_id = f"JS-{'-'.join(sorted_entity_ids)}-{date_part}"
                        state["关联实体ID列表"] = sorted_entity_ids
                        state["状态ID"] = new_state_id
                        id_mapping[original_state_id] = new_state_id
                        self.validation_report["warnings_modified"].append(f"已重新排序联合状态ID：{original_state_id} -> {new_state_id}")

            # 处理区分码唯一性
            entity_ids_tuple = tuple(sorted(entity_ids))
            key = (state_type, entity_ids_tuple, time_range)
            need_code = group_need_code.get(key, False)
            # 生成标准ID（不带区分码）
            time_match = self.time_pattern.match(state["时间"])
            if time_match:
                start_date = f"{time_match.group(1)}{time_match.group(2)}{time_match.group(3)}"
                end_date = f"{time_match.group(4)}{time_match.group(5)}{time_match.group(6)}"
                date_part = f"{start_date}_{end_date}"
                if state_type == "独立状态" and len(entity_ids) == 1:
                    entity_id = entity_ids[0]
                    if entity_id.startswith("E-"):
                        base_id = f"ES-{entity_id}-{date_part}"
                    elif entity_id.startswith("L-"):
                        base_id = f"LS-{entity_id}-{date_part}"
                    elif entity_id.startswith("F-"):
                        base_id = f"FS-{entity_id}-{date_part}"
                    else:
                        base_id = f"ES-{entity_id}-{date_part}"
                elif state_type == "联合状态" and len(entity_ids) >= 2:
                    entity_part = "-".join(sorted(entity_ids))
                    base_id = f"JS-{entity_part}-{date_part}"
                else:
                    base_id = state_id
            else:
                base_id = state_id

            # 检查是否需要加区分码
            if need_code:
                code = group_code_count[key]
                group_code_count[key] += 1
                new_state_id = f"{base_id}-{code}"
                if state["状态ID"] != new_state_id:
                    id_mapping[state["状态ID"]] = new_state_id
                    state["状态ID"] = new_state_id
                    self.validation_report["warnings_modified"].append(f"同组状态ID唯一性处理，添加区分码：{original_state_id} -> {new_state_id}")
            else:
                # 不需要区分码，保持简洁
                if state["状态ID"] != base_id:
                    id_mapping[state["状态ID"]] = base_id
                    state["状态ID"] = base_id
                    self.validation_report["warnings_modified"].append(f"状态ID唯一性处理，去除区分码：{original_state_id} -> {base_id}")

            valid_states.append(state)

        # 更新所有状态关系中的ID引用
        if id_mapping:
            valid_relations = self._update_state_relation_references(valid_relations, id_mapping)
        return valid_states, valid_relations
