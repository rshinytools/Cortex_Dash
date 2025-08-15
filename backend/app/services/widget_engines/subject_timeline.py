# ABOUTME: Subject Timeline widget engine implementation
# ABOUTME: Handles individual subject journey visualization with events, visits, and milestones

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from app.services.widget_engines.base_widget import WidgetEngine
from app.models.phase1_models import AggregationType, DataGranularity, JoinType


class SubjectTimelineEngine(WidgetEngine):
    """Engine for Subject Timeline widgets"""
    
    def get_data_contract(self) -> Dict[str, Any]:
        """Return Subject Timeline data contract"""
        return {
            "granularity": DataGranularity.EVENT_LEVEL,
            "required_fields": [
                {"name": "subject_id_field", "type": "string", "description": "Subject identifier"},
                {"name": "event_date_field", "type": "date", "description": "Event date/time"},
                {"name": "event_type_field", "type": "categorical", "description": "Type of event"}
            ],
            "optional_fields": [
                {"name": "event_name_field", "type": "string", "description": "Event name/description"},
                {"name": "event_value_field", "type": "any", "description": "Event value/result"},
                {"name": "event_category_field", "type": "categorical", "description": "Event category"},
                {"name": "event_status_field", "type": "categorical", "description": "Event status"},
                {"name": "event_duration_field", "type": "numeric", "description": "Event duration"},
                {"name": "reference_date_field", "type": "date", "description": "Reference date for relative timing"}
            ],
            "supported_aggregations": [
                AggregationType.COUNT,
                AggregationType.MIN,
                AggregationType.MAX
            ],
            "supports_grouping": True,
            "supports_filtering": True,
            "supports_joins": True,
            "max_join_datasets": 4,
            "recommended_cache_ttl": 3600
        }
    
    def validate_mapping(self) -> Tuple[bool, List[str]]:
        """Validate Subject Timeline mapping"""
        errors = []
        
        mappings = self.mapping_config.get("field_mappings", {})
        
        # Check required fields
        if "subject_id_field" not in mappings:
            errors.append("subject_id_field is required")
        if "event_date_field" not in mappings:
            errors.append("event_date_field is required")
        if "event_type_field" not in mappings:
            errors.append("event_type_field is required")
        
        # Validate timeline configuration
        timeline_config = self.mapping_config.get("timeline_config", {})
        view_type = timeline_config.get("view_type", "chronological")
        
        if view_type not in ["chronological", "grouped", "swim_lane", "gantt"]:
            errors.append(f"Invalid view_type: {view_type}")
        
        return len(errors) == 0, errors
    
    def build_query(self) -> str:
        """Build SQL query for subject timeline"""
        mappings = self.mapping_config.get("field_mappings", {})
        dataset = self.mapping_config.get("primary_dataset", "dataset")
        timeline_config = self.mapping_config.get("timeline_config", {})
        
        # Get field mappings
        subject_id = mappings.get("subject_id_field", {}).get("source_field")
        event_date = mappings.get("event_date_field", {}).get("source_field")
        event_type = mappings.get("event_type_field", {}).get("source_field")
        event_name = mappings.get("event_name_field", {}).get("source_field")
        event_value = mappings.get("event_value_field", {}).get("source_field")
        event_category = mappings.get("event_category_field", {}).get("source_field")
        event_status = mappings.get("event_status_field", {}).get("source_field")
        event_duration = mappings.get("event_duration_field", {}).get("source_field")
        reference_date = mappings.get("reference_date_field", {}).get("source_field")
        
        # Build SELECT clause
        select_parts = [
            f"{subject_id} as subject_id",
            f"{event_date} as event_date",
            f"{event_type} as event_type"
        ]
        
        # Add optional fields
        if event_name:
            select_parts.append(f"{event_name} as event_name")
        if event_value:
            select_parts.append(f"{event_value} as event_value")
        if event_category:
            select_parts.append(f"{event_category} as event_category")
        if event_status:
            select_parts.append(f"{event_status} as event_status")
        if event_duration:
            select_parts.append(f"{event_duration} as event_duration")
        
        # Calculate relative timing if reference date provided
        if reference_date:
            select_parts.append(f"{event_date} - {reference_date} as days_from_reference")
            select_parts.append(f"{reference_date} as reference_date")
        else:
            # Calculate days from first event
            select_parts.append(f"""
                {event_date} - MIN({event_date}) OVER (PARTITION BY {subject_id}) as days_from_start
            """)
        
        # Add event sequence number
        select_parts.append(f"""
            ROW_NUMBER() OVER (PARTITION BY {subject_id} ORDER BY {event_date}) as event_sequence
        """)
        
        # Add time to next event
        select_parts.append(f"""
            LEAD({event_date}) OVER (PARTITION BY {subject_id} ORDER BY {event_date}) - {event_date} as days_to_next
        """)
        
        # Build FROM clause
        from_clause = f"FROM {dataset}"
        
        # Build JOIN clause
        join_clause = self.build_join_clause()
        
        # Build WHERE clause
        where_clause = self.build_where_clause()
        
        # Add subject filter if specified
        subject_filter = self.mapping_config.get("subject_filter")
        if subject_filter:
            if isinstance(subject_filter, list):
                subjects = "', '".join(str(s) for s in subject_filter)
                subject_condition = f"{subject_id} IN ('{subjects}')"
            else:
                subject_condition = f"{subject_id} = '{subject_filter}'"
            
            if where_clause:
                where_clause += f" AND {subject_condition}"
            else:
                where_clause = f"WHERE {subject_condition}"
        
        # Add date range filter
        date_range = timeline_config.get("date_range", {})
        if date_range:
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            if start_date and end_date:
                date_filter = f"{event_date} BETWEEN '{start_date}' AND '{end_date}'"
                if where_clause:
                    where_clause += f" AND {date_filter}"
                else:
                    where_clause = f"WHERE {date_filter}"
        
        # Build ORDER BY clause
        order_by_parts = [subject_id, event_date]
        if event_type:
            order_by_parts.append(event_type)
        order_by_clause = f"ORDER BY {', '.join(order_by_parts)}"
        
        # Apply limit if specified
        limit = timeline_config.get("max_events_per_subject")
        limit_clause = ""
        if limit:
            # Use window function to limit events per subject
            base_query = f"""
                SELECT {', '.join(select_parts)}
                {from_clause}
                {join_clause}
                {where_clause}
            """
            
            query = f"""
                WITH ranked_events AS (
                    SELECT *,
                        ROW_NUMBER() OVER (PARTITION BY subject_id ORDER BY event_date) as rn
                    FROM ({base_query}) as base
                )
                SELECT * FROM ranked_events
                WHERE rn <= {limit}
                {order_by_clause}
            """
        else:
            query = f"""
                SELECT {', '.join(select_parts)}
                {from_clause}
                {join_clause}
                {where_clause}
                {order_by_clause}
            """
        
        return query.strip()
    
    def group_events_by_category(self, events: List[Dict]) -> Dict[str, List[Dict]]:
        """Group events by category for swim lane view"""
        grouped = {}
        
        for event in events:
            category = event.get("event_category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(event)
        
        # Sort events within each category
        for category in grouped:
            grouped[category].sort(key=lambda x: x.get("event_date", ""))
        
        return grouped
    
    def calculate_milestones(self, events: List[Dict]) -> List[Dict]:
        """Identify and calculate milestone events"""
        milestones = []
        milestone_config = self.mapping_config.get("milestone_config", {})
        
        # Get milestone definitions
        milestone_types = milestone_config.get("types", [])
        
        for event in events:
            event_type = event.get("event_type")
            
            # Check if this event is a milestone
            is_milestone = False
            milestone_info = {}
            
            for milestone_def in milestone_types:
                if milestone_def.get("event_type") == event_type:
                    is_milestone = True
                    milestone_info = {
                        "label": milestone_def.get("label", event_type),
                        "icon": milestone_def.get("icon"),
                        "color": milestone_def.get("color"),
                        "importance": milestone_def.get("importance", "normal")
                    }
                    break
            
            if is_milestone:
                milestones.append({
                    **event,
                    "is_milestone": True,
                    "milestone_info": milestone_info
                })
        
        return milestones
    
    def build_gantt_data(self, events: List[Dict]) -> List[Dict]:
        """Build Gantt chart data from events"""
        gantt_data = []
        
        # Group consecutive events of same type
        current_task = None
        
        for event in events:
            event_type = event.get("event_type")
            event_date = event.get("event_date")
            duration = event.get("event_duration", 1)
            
            if current_task and current_task["type"] == event_type:
                # Extend current task
                current_task["end_date"] = event_date
                current_task["duration"] += duration
                current_task["events"].append(event)
            else:
                # Start new task
                if current_task:
                    gantt_data.append(current_task)
                
                current_task = {
                    "type": event_type,
                    "start_date": event_date,
                    "end_date": event_date,
                    "duration": duration,
                    "events": [event],
                    "status": event.get("event_status", "completed")
                }
        
        # Add last task
        if current_task:
            gantt_data.append(current_task)
        
        return gantt_data
    
    def calculate_statistics(self, subject_events: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate timeline statistics"""
        stats = {
            "total_subjects": len(subject_events),
            "total_events": sum(len(events) for events in subject_events.values()),
            "event_types": {},
            "duration_stats": {},
            "completion_rates": {}
        }
        
        # Collect all events
        all_events = []
        for events in subject_events.values():
            all_events.extend(events)
        
        # Count event types
        event_type_counts = {}
        for event in all_events:
            event_type = event.get("event_type", "Unknown")
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        stats["event_types"] = event_type_counts
        
        # Calculate duration statistics
        durations = []
        for subject_id, events in subject_events.items():
            if len(events) >= 2:
                first_event = min(events, key=lambda x: x.get("event_date", ""))
                last_event = max(events, key=lambda x: x.get("event_date", ""))
                
                # Calculate study duration for this subject
                # This would need proper date parsing in real implementation
                duration_days = events[-1].get("days_from_start", 0)
                if duration_days:
                    durations.append(duration_days)
        
        if durations:
            stats["duration_stats"] = {
                "min_days": min(durations),
                "max_days": max(durations),
                "avg_days": sum(durations) / len(durations),
                "median_days": sorted(durations)[len(durations) // 2]
            }
        
        # Calculate completion rates
        milestone_config = self.mapping_config.get("milestone_config", {})
        required_milestones = [m["event_type"] for m in milestone_config.get("types", []) 
                               if m.get("required", False)]
        
        if required_milestones:
            completed_subjects = 0
            for subject_id, events in subject_events.items():
                subject_event_types = set(e.get("event_type") for e in events)
                if all(rm in subject_event_types for rm in required_milestones):
                    completed_subjects += 1
            
            stats["completion_rates"]["overall"] = (completed_subjects / len(subject_events) * 100) if subject_events else 0
        
        return stats
    
    def transform_results(self, raw_data: List[Dict]) -> Dict[str, Any]:
        """Transform raw results into subject timeline format"""
        
        if not raw_data:
            return {
                "widget_type": "subject_timeline",
                "view_type": self.mapping_config.get("timeline_config", {}).get("view_type", "chronological"),
                "subjects": [],
                "statistics": {},
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "event_count": 0
                }
            }
        
        timeline_config = self.mapping_config.get("timeline_config", {})
        view_type = timeline_config.get("view_type", "chronological")
        
        # Group events by subject
        subject_events = {}
        for event in raw_data:
            subject_id = event.get("subject_id")
            if subject_id not in subject_events:
                subject_events[subject_id] = []
            subject_events[subject_id].append(event)
        
        # Build timeline data based on view type
        timeline_data = []
        
        for subject_id, events in subject_events.items():
            # Sort events chronologically
            events.sort(key=lambda x: x.get("event_date", ""))
            
            subject_timeline = {
                "subject_id": subject_id,
                "event_count": len(events),
                "first_event": events[0].get("event_date") if events else None,
                "last_event": events[-1].get("event_date") if events else None,
                "duration_days": events[-1].get("days_from_start", 0) if events else 0
            }
            
            if view_type == "chronological":
                # Simple chronological list
                subject_timeline["events"] = events
                
            elif view_type == "grouped":
                # Group by category
                subject_timeline["event_groups"] = self.group_events_by_category(events)
                
            elif view_type == "swim_lane":
                # Swim lane view with categories
                subject_timeline["lanes"] = self.group_events_by_category(events)
                
            elif view_type == "gantt":
                # Gantt chart view
                subject_timeline["tasks"] = self.build_gantt_data(events)
            
            # Add milestones
            milestones = self.calculate_milestones(events)
            if milestones:
                subject_timeline["milestones"] = milestones
                subject_timeline["milestone_count"] = len(milestones)
            
            # Calculate subject-specific metrics
            event_types = list(set(e.get("event_type") for e in events))
            subject_timeline["event_types"] = event_types
            subject_timeline["unique_event_types"] = len(event_types)
            
            # Add status summary
            if any("event_status" in e for e in events):
                status_counts = {}
                for e in events:
                    status = e.get("event_status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                subject_timeline["status_summary"] = status_counts
            
            timeline_data.append(subject_timeline)
        
        # Calculate overall statistics
        statistics = self.calculate_statistics(subject_events)
        
        # Build response
        response = {
            "widget_type": "subject_timeline",
            "view_type": view_type,
            "subjects": timeline_data,
            "statistics": statistics,
            "timeline_config": {
                "show_milestones": timeline_config.get("show_milestones", True),
                "show_connections": timeline_config.get("show_connections", False),
                "group_by": timeline_config.get("group_by"),
                "date_format": timeline_config.get("date_format", "YYYY-MM-DD"),
                "relative_dates": timeline_config.get("relative_dates", False)
            },
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "subject_count": len(subject_events),
                "event_count": sum(len(events) for events in subject_events.values()),
                "date_range": {
                    "start": min(e.get("event_date", "") for e in raw_data) if raw_data else None,
                    "end": max(e.get("event_date", "") for e in raw_data) if raw_data else None
                }
            }
        }
        
        # Add legend if categories are used
        if any("event_category" in e for e in raw_data):
            categories = list(set(e.get("event_category", "Other") for e in raw_data))
            response["legend"] = {
                "categories": categories,
                "colors": timeline_config.get("category_colors", {})
            }
        
        # Add filters if configured
        if timeline_config.get("filterable", False):
            response["available_filters"] = {
                "event_types": list(set(e.get("event_type") for e in raw_data if e.get("event_type"))),
                "event_categories": list(set(e.get("event_category") for e in raw_data if e.get("event_category"))),
                "event_statuses": list(set(e.get("event_status") for e in raw_data if e.get("event_status")))
            }
        
        return response