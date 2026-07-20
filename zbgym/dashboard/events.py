"""Dashboard event definitions for ZBGym.

This module defines all event types that can be published
to the Dashboard during training.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zbgym.dashboard.models import EventData


class Event:
    """Event factory for creating standardized events.

    This class provides methods to create properly formatted
    event data for common training events.

    Example:
        event = Event.character_spawn(
            session_id="abc123",
            character_id="player_1",
            character_type="Soldier",
            position={"x": 100, "y": 200}
        )
    """

    @staticmethod
    def character_spawn(
        session_id: str,
        character_id: str,
        character_type: str,
        position: dict[str, float],
    ) -> EventData:
        """Create character spawn event.

        Args:
            session_id: Session ID.
            character_id: Unique character identifier.
            character_type: Type/class of character.
            position: Spawn position.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.CHARACTER_SPAWN,
            data={
                "character_id": character_id,
                "character_type": character_type,
                "position": position,
            },
            actor=character_id,
        )

    @staticmethod
    def character_death(
        session_id: str,
        character_id: str,
        killer_id: str | None = None,
        cause: str = "eliminated",
        position: dict[str, float] | None = None,
    ) -> EventData:
        """Create character death event.

        Args:
            session_id: Session ID.
            character_id: Character that died.
            killer_id: Character that killed (if applicable).
            cause: Cause of death.
            position: Death position.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        data: dict = {
            "cause": cause,
        }
        if killer_id:
            data["killer_id"] = killer_id
        if position:
            data["position"] = position

        return EventData.create(
            session_id=session_id,
            event_type=EventType.CHARACTER_DEATH,
            data=data,
            actor=character_id,
        )

    @staticmethod
    def kill(
        session_id: str,
        killer_id: str,
        victim_id: str,
        weapon: str | None = None,
        position: dict[str, float] | None = None,
    ) -> EventData:
        """Create kill event.

        Args:
            session_id: Session ID.
            killer_id: Character that got the kill.
            victim_id: Character that was killed.
            weapon: Weapon used (if applicable).
            position: Kill position.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        data: dict = {
            "victim_id": victim_id,
        }
        if weapon:
            data["weapon"] = weapon
        if position:
            data["position"] = position

        return EventData.create(
            session_id=session_id,
            event_type=EventType.KILL,
            data=data,
            actor=killer_id,
        )

    @staticmethod
    def projectile_fired(
        session_id: str,
        character_id: str,
        projectile_id: str,
        weapon: str,
        position: dict[str, float],
        direction: dict[str, float],
    ) -> EventData:
        """Create projectile fired event.

        Args:
            session_id: Session ID.
            character_id: Character that fired.
            projectile_id: Unique projectile identifier.
            weapon: Weapon used.
            position: Fire position.
            direction: Projectile direction.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.PROJECTILE_FIRED,
            data={
                "projectile_id": projectile_id,
                "weapon": weapon,
                "position": position,
                "direction": direction,
            },
            actor=character_id,
        )

    @staticmethod
    def projectile_hit(
        session_id: str,
        projectile_id: str,
        target_id: str,
        damage: float,
        position: dict[str, float],
    ) -> EventData:
        """Create projectile hit event.

        Args:
            session_id: Session ID.
            projectile_id: Projectile that hit.
            target_id: Target that was hit.
            damage: Damage dealt.
            position: Hit position.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.PROJECTILE_HIT,
            data={
                "projectile_id": projectile_id,
                "target_id": target_id,
                "damage": damage,
                "position": position,
            },
            actor=target_id,
        )

    @staticmethod
    def collision(
        session_id: str,
        entity_a: str,
        entity_b: str,
        collision_type: str,
        position: dict[str, float],
    ) -> EventData:
        """Create collision event.

        Args:
            session_id: Session ID.
            entity_a: First entity involved.
            entity_b: Second entity involved.
            collision_type: Type of collision.
            position: Collision position.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.COLLISION,
            data={
                "entity_a": entity_a,
                "entity_b": entity_b,
                "collision_type": collision_type,
                "position": position,
            },
        )

    @staticmethod
    def safe_zone_shrink(
        session_id: str,
        old_radius: float,
        new_radius: float,
        duration: float,
    ) -> EventData:
        """Create safe zone shrink event.

        Args:
            session_id: Session ID.
            old_radius: Previous zone radius.
            new_radius: New zone radius.
            duration: Time until full shrink.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.SAFE_ZONE_SHRINK,
            data={
                "old_radius": old_radius,
                "new_radius": new_radius,
                "duration": duration,
            },
        )

    @staticmethod
    def safe_zone_expand(
        session_id: str,
        old_radius: float,
        new_radius: float,
        duration: float,
    ) -> EventData:
        """Create safe zone expand event.

        Args:
            session_id: Session ID.
            old_radius: Previous zone radius.
            new_radius: New zone radius.
            duration: Time until full expand.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.SAFE_ZONE_EXPAND,
            data={
                "old_radius": old_radius,
                "new_radius": new_radius,
                "duration": duration,
            },
        )

    @staticmethod
    def plugin_loaded(
        session_id: str,
        plugin_id: str,
        plugin_name: str,
        version: str,
    ) -> EventData:
        """Create plugin loaded event.

        Args:
            session_id: Session ID.
            plugin_id: Plugin identifier.
            plugin_name: Plugin name.
            version: Plugin version.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.PLUGIN_LOADED,
            data={
                "plugin_id": plugin_id,
                "plugin_name": plugin_name,
                "version": version,
            },
        )

    @staticmethod
    def replay_saved(
        session_id: str,
        file_path: str,
        file_size: int,
        episode: int,
        duration: float,
    ) -> EventData:
        """Create replay saved event.

        Args:
            session_id: Session ID.
            file_path: Path to saved replay.
            file_size: Size of replay file.
            episode: Episode number.
            duration: Replay duration.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.REPLAY_SAVED,
            data={
                "file_path": file_path,
                "file_size": file_size,
                "episode": episode,
                "duration": duration,
            },
        )

    @staticmethod
    def training_started(
        session_id: str,
        env_id: str,
        trainer: str,
        total_timesteps: int,
    ) -> EventData:
        """Create training started event.

        Args:
            session_id: Session ID.
            env_id: Environment ID.
            trainer: Training algorithm.
            total_timesteps: Target timesteps.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.TRAINING_STARTED,
            data={
                "env_id": env_id,
                "trainer": trainer,
                "total_timesteps": total_timesteps,
            },
        )

    @staticmethod
    def training_finished(
        session_id: str,
        total_timesteps: int,
        duration: float,
        final_reward: float | None = None,
    ) -> EventData:
        """Create training finished event.

        Args:
            session_id: Session ID.
            total_timesteps: Total timesteps completed.
            duration: Total training duration.
            final_reward: Final mean reward.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        data: dict = {
            "total_timesteps": total_timesteps,
            "duration": duration,
        }
        if final_reward is not None:
            data["final_reward"] = final_reward

        return EventData.create(
            session_id=session_id,
            event_type=EventType.TRAINING_FINISHED,
            data=data,
        )

    @staticmethod
    def custom(
        session_id: str,
        event_name: str,
        event_data: dict,
    ) -> EventData:
        """Create a custom event.

        Args:
            session_id: Session ID.
            event_name: Name of the custom event.
            event_data: Custom event data.

        Returns:
            EventData instance.
        """
        from zbgym.dashboard.models import EventData, EventType

        return EventData.create(
            session_id=session_id,
            event_type=EventType.CUSTOM,
            data={
                "event_name": event_name,
                **event_data,
            },
        )
