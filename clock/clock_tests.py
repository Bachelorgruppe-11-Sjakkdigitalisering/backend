from clock.logic import ClockLogic
from clock.state import StableTimeTracker

def test_clock_filters():
    print("--- TEST AV PARSE_TO_SECONDS ---")
    # Correct string: 05:00 (300 seconds)
    print(f"Normal tid '0500' -> {ClockLogic.parse_to_seconds('0500')}") 
    
    # YOLO detecting a '.'
    print(f"Støy i streng '05.00' -> {ClockLogic.parse_to_seconds('05.00')}")
    
    # YOLO hallucinating an extra number (jumps over an hour)
    hallusinasjon = ClockLogic.parse_to_seconds('010500', reference_seconds=300)
    print(f"Hallusinasjon '010500' blokkert? -> {'JA (Returnerte None)' if hallusinasjon is None else 'NEI'}")

    print("\n--- TEST AV STABLE TIME TRACKER ---")
    tracker = StableTimeTracker(required_consistency=8)
    
    # Sends correct time 10 times
    for _ in range(10):
        tracker.update(300)
    print(f"Tracker verdi etter stabil tid: {tracker.value}")
    
    # Small inconsistency after 3 frames
    tracker.update(295)
    tracker.update(295)
    tracker.update(295)
    
    # Correct time again
    tracker.update(299)
    print(f"Tracker verdi etter 3 frames med støy: {tracker.value} (Støy ignorert!)")

test_clock_filters()