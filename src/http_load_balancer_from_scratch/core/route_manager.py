from __future__ import annotations

import pandas as pd
from pathlib import Path
from uuid import uuid4
from http_load_balancer_from_scratch.schemas.route_schema import RouteSchema
from http_load_balancer_from_scratch.settings import settings

class RouteManager:
    ROUTE_COLUMNS: tuple[str, ...] = ("route_id", "host", "port")

    @classmethod
    def _load_frame(cls) -> pd.DataFrame:
        path = settings.CONFIG_FILE_PATH
        if path.stat().st_size == 0:
            return pd.DataFrame(columns=cls.ROUTE_COLUMNS)

        frame = pd.read_csv(path)
        if frame.empty:
            return pd.DataFrame(columns=cls.ROUTE_COLUMNS)

        missing_columns = [column for column in cls.ROUTE_COLUMNS if column not in frame.columns]
        if missing_columns:
            raise ValueError(f"Missing required route columns: {', '.join(missing_columns)}")

        return frame.loc[:, cls.ROUTE_COLUMNS].copy()

    @classmethod
    def _save_frame(cls, frame: pd.DataFrame) -> None:
        path = settings.CONFIG_FILE_PATH
        frame = frame.loc[:, cls.ROUTE_COLUMNS].copy()
        frame.to_csv(path, index=False)

    @classmethod
    def get_routes(cls) -> list[RouteSchema]:
        frame = cls._load_frame()
        if frame.empty:
            return []

        return [
            RouteSchema(
                route_id=str(row.route_id),
                host=str(row.host),
                port=int(row.port),
            )
            for row in frame.itertuples(index=False)
        ]

    @classmethod
    def add_route(cls, host: str, port: int, route_id: str | None = None) -> RouteSchema:
        route = RouteSchema(
            route_id=route_id or uuid4().hex,
            host=host,
            port=port,
        )

        frame = cls._load_frame()
        updated_frame = pd.concat(
            [
                frame,
                pd.DataFrame(
                    [{"route_id": route.route_id, "host": route.host, "port": route.port}]
                ),
            ],
            ignore_index=True,
        )
        cls._save_frame(updated_frame)
        return route

    @classmethod
    def remove_route(cls, route_id: str) -> bool:
        frame = cls._load_frame()
        if frame.empty:
            return False

        filtered_frame = frame.loc[frame["route_id"] != route_id].copy()
        if len(filtered_frame) == len(frame):
            return False

        cls._save_frame(filtered_frame)
        return True
