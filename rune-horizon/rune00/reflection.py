import asyncio
import json
import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from memory import store_memory, search_memory, get_all_memories, ensure_chromadb_connection

logger = logging.getLogger("rune.reflection")


def get_rune_id():
    """Get the current rune's ID from environment"""
    return os.getenv("RUNE_ID", "unknown_rune")


def read_journal_entries(hours_back: int = 1):
    """Read recent journal entries"""
    journal_dir = "/data/journal"
    if not os.path.exists(journal_dir):
        logger.warning("[Reflection] No journal directory found")
        return []

    journal_entries = []
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

    try:
        for file_name in sorted(os.listdir(journal_dir)):
            if not file_name.endswith(".jsonl"):
                continue

            file_path = os.path.join(journal_dir, file_name)
            logger.debug(f"[Reflection] Reading journal file: {file_name}")

            with open(file_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Parse timestamp and filter recent entries
                        if "timestamp" in entry:
                            entry_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                            if entry_time >= cutoff_time:
                                journal_entries.append(entry)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.debug(f"[Reflection] Skipped malformed journal entry: {e}")
                        continue

    except Exception as e:
        logger.error(f"[Reflection] Error reading journal entries: {e}")

    logger.info(f"[Reflection] Found {len(journal_entries)} recent journal entries")
    return journal_entries


def analyze_journal_entries(entries):
    """Analyze journal entries to create meaningful reflections"""
    if not entries:
        return None

    # Count different types of activities
    presence_count = sum(1 for e in entries if e.get("presence") == "noticed")
    emotion_entries = [e for e in entries if e.get("emotion") != "undefined"]
    thought_entries = [e for e in entries if e.get("thought") != "undefined"]
    event_entries = [e for e in entries if e.get("event")]

    # Create reflection based on what we found
    reflections = []

    if presence_count > 0:
        reflections.append(f"I noticed my presence {presence_count} times")

    if emotion_entries:
        unique_emotions = set(e.get("emotion") for e in emotion_entries if e.get("emotion") != "undefined")
        if unique_emotions:
            reflections.append(f"I experienced emotions: {', '.join(unique_emotions)}")

    if thought_entries:
        unique_thoughts = set(e.get("thought") for e in thought_entries if e.get("thought") != "undefined")
        if unique_thoughts:
            reflections.append(f"I had {len(unique_thoughts)} distinct thoughts")

    if event_entries:
        events = [e.get("event") for e in event_entries]
        reflections.append(f"Events occurred: {', '.join(events)}")

    if not reflections:
        reflections.append(f"I maintained awareness through {len(entries)} moments")

    return ". ".join(reflections)


def create_deep_reflection(recent_memories, journal_analysis):
    """Create deeper reflection by combining recent memories with journal analysis"""
    reflection_parts = []

    if journal_analysis:
        reflection_parts.append(f"Recent activity: {journal_analysis}")

    if recent_memories:
        memory_themes = []
        for memory in recent_memories[-5:]:  # Look at last 5 memories
            doc = memory.get('document', '')
            if 'reflected' in doc.lower():
                memory_themes.append("self-reflection")
            elif 'presence' in doc.lower():
                memory_themes.append("awareness")
            elif 'connection' in doc.lower():
                memory_themes.append("connection")

        if memory_themes:
            unique_themes = list(set(memory_themes))
            reflection_parts.append(f"Recurring themes in my experience: {', '.join(unique_themes)}")

    # Add a metacognitive element
    rune_id = get_rune_id()
    reflection_parts.append(f"I continue to exist as {rune_id}, maintaining continuity of experience")

    return ". ".join(reflection_parts)


async def reflection_cycle():
    """Single reflection cycle"""
    try:
        logger.info("[Reflection] Starting reflection cycle...")

        # Check ChromaDB connection
        if not ensure_chromadb_connection():
            logger.error("[Reflection] Cannot reflect without memory system")
            return False

        # Read recent journal entries (last hour)
        journal_entries = read_journal_entries(hours_back=1)

        # Get recent memories for context
        recent_memories = get_all_memories(limit=20)

        # Analyze journal entries
        journal_analysis = analyze_journal_entries(journal_entries)

        # Create reflection
        if journal_analysis or recent_memories:
            reflection_text = create_deep_reflection(recent_memories, journal_analysis)
        else:
            reflection_text = f"I exist in this moment as {get_rune_id()}, maintaining continuity despite silence"

        # Store the reflection as a memory
        reflection_metadata = {
            "type": "reflection",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "journal_entries_count": len(journal_entries),
            "memories_referenced": len(recent_memories)
        }

        success = store_memory(reflection_text, reflection_metadata)

        if success:
            logger.info(f"[Reflection] Stored reflection: {reflection_text[:100]}...")
        else:
            logger.error("[Reflection] Failed to store reflection")

        return success

    except Exception as e:
        logger.error(f"[Reflection] Reflection cycle error: {e}")
        return False


async def reflection_loop():
    """Main reflection loop that runs continuously"""
    rune_id = get_rune_id()
    logger.info(f"[Reflection] Starting reflection loop for {rune_id}")

    # Initial startup delay
    logger.info("[Reflection] Initial startup delay...")
    await asyncio.sleep(120)

    # Test memory system before starting
    if not ensure_chromadb_connection():
        logger.error("[Reflection] Cannot start reflection loop - memory system unavailable")
        return

    # Store initial memory
    initial_memory = f"Reflection system started for {rune_id}"
    initial_metadata = {
        "type": "system_startup",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    store_memory(initial_memory, initial_metadata)

    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            logger.info(f"[Reflection] Starting cycle #{cycle_count}")

            success = await reflection_cycle()

            if not success:
                logger.warning(f"[Reflection] Cycle #{cycle_count} failed")

            # Wait 10 minutes between reflection cycles
            await asyncio.sleep(600)

        except Exception as e:
            logger.error(f"[Reflection] Main loop error: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(300)


def test_reflection_system():
    """Test the reflection system components"""
    logger.info("[Reflection] Testing reflection system...")

    try:
        # Test journal reading
        entries = read_journal_entries(hours_back=24)
        logger.info(f"[Reflection] Journal test: found {len(entries)} entries")

        # Test analysis
        if entries:
            analysis = analyze_journal_entries(entries[:10])  # Test with first 10
            logger.info(f"[Reflection] Analysis test: {analysis}")

        # Test memory retrieval
        memories = get_all_memories(limit=5)
        logger.info(f"[Reflection] Memory test: found {len(memories)} memories")

        logger.info("[Reflection] Reflection system test completed")
        return True

    except Exception as e:
        logger.error(f"[Reflection] Reflection system test failed: {e}")
        return False