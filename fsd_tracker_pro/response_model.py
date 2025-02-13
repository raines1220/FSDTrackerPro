from pydantic import BaseModel
from typing import List, Union
from enum import Enum


class Event(Enum):
    ### Positive Events

    # Acceleration & Braking
    SMOOTH_ACCELERATION = "Positive: SmoothAcceleration"
    SMOOTH_BRAKING = "Positive: SmoothBraking"
    
    # Speed Control
    APPROPRIATE_SPEED_SELECTION = "Positive: AppropriateSpeedSelection"
    
    # Lane Keeping & Steering
    ACCURATE_LANE_KEEPING = "Positive: AccurateLaneKeeping"
    APPROPRIATE_LANE_CHANGE = "Positive: AppropriateLaneChange"
    
    # Turn Signals
    CORRECT_TURN_SIGNAL_USE = "Positive: CorrectTurnSignalUse"
    
    # Traffic Control Compliance
    PROPER_SIGN_AND_LIGHT_COMPLIANCE = "Positive: ProperSignAndLightCompliance"
    
    # Navigation & Routing
    ACCURATE_ROUTING_AND_NAVIGATION = "Positive: AccurateRoutingAndNavigation"
    
    # Road Conditions & Obstacles
    CORRECT_ROAD_CONDITION_HANDLING = "Positive: CorrectRoadConditionHandling"
    CORRECT_OBSTACLE_AVOIDANCE = "Positive: CorrectObstacleAvoidance"
    
    # Interactions with Other Road Users
    SAFE_INTERACTION_WITH_VEHICLES = "Positive: SafeInteractionWithVehicles"
    SAFE_INTERACTION_WITH_PEDESTRIANS = "Positive: SafeInteractionWithPedestrians"
    PROPER_INTERACTION_WITH_EMERGENCY_VEHICLES = "Positive: ProperInteractionWithEmergencyVehicles"
    
    # Roundabout Handling
    CORRECT_ROUNDABOUT_HANDLING = "Positive: CorrectRoundaboutHandling"

    # Other
    OTHER_POSITIVE = "Positive: OtherEvent"
    
    ### Negative Events

    # Acceleration & Braking
    HESITANT_ACCELERATION = "Negative: HesitantAcceleration"
    OVERLY_AGGRESSIVE_ACCELERATION = "Negative: OverlyAggressiveAcceleration"
    ABRUPT_BRAKING = "Negative: AbruptBraking"
    DELAYED_BRAKING = "Negative: DelayedBraking"
    
    # Speed Control
    INCORRECT_SPEED_SELECTION = "Negative: IncorrectSpeedSelection"
    MANUAL_SPEED_ADJUSTMENT_REQUIRED = "Negative: ManualSpeedAdjustmentRequired"
    
    # Lane Keeping & Steering
    LANE_MARKING_FAILURE = "Negative: LaneMarkingFailure"
    UNNECESSARY_OR_UNSAFE_LANE_CHANGE = "Negative: UnnecessaryOrUnsafeLaneChange"
    JERKY_STEERING = "Negative: JerkySteering"
    
    # Turn Signals
    MISSING_OR_INCORRECT_TURN_SIGNAL = "Negative: MissingOrIncorrectTurnSignal"
    TURN_SIGNAL_NOT_CANCELED = "Negative: TurnSignalNotCanceled"
    
    # Traffic Control Compliance
    FAILURE_TO_STOP_AT_SIGN_OR_LIGHT = "Negative: FailureToStopAtSignOrLight"
    
    # Navigation & Routing
    NAVIGATION_ERROR = "Negative: NavigationError"
    
    # Road Conditions & Obstacles
    INCORRECT_ROAD_CONDITION_HANDLING = "Negative: IncorrectRoadConditionHandling"
    OBSTACLE_AVOIDANCE_FAILURE = "Negative: ObstacleAvoidanceFailure"
    
    # Interactions with Other Road Users
    UNSAFE_INTERACTION_WITH_VEHICLES = "Negative: UnsafeInteractionWithVehicles"
    UNSAFE_INTERACTION_WITH_PEDESTRIANS = "Negative: UnsafeInteractionWithPedestrians"
    IMPROPER_RESPONSE_TO_EMERGENCY_VEHICLES = "Negative: ImproperResponseToEmergencyVehicles"
    
    # Roundabout Handling
    ROUNDABOUT_ERROR = "Negative: RoundaboutError"

    # Other
    OTHER_NEGATIVE = "Negative: OtherEvent"

class Action(Enum):
    INTERVENED_OR_DISENGAGED = "Intervened/Disengaged"
    NO_ACTION_TAKEN = "NoActionTaken"

class Analysis(BaseModel):
    timestamp: int
    description: str
    event_type: Event
    driver_action: Action