import random
import json
import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import TriviaQuestion, TriviaAnswer, TriviaStat


class TriviaService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_trivia_question(
        self,
        question: str,
        options: list[str],
        correct_answer: int,
        category: str,
        difficulty: str,
        channel_access: str,
        lore_piece: str | None = None,
    ) -> TriviaQuestion:
        """Store a new trivia question."""
        q = TriviaQuestion(
            question=question,
            options=json.dumps(options, ensure_ascii=False),
            correct_answer=correct_answer,
            category=category,
            difficulty=difficulty,
            channel_access=channel_access,
            lore_piece=lore_piece,
        )
        self.session.add(q)
        await self.session.commit()
        await self.session.refresh(q)
        return q

    async def get_random_question(
        self,
        user_access: str = "free",
        difficulty: str | None = None,
        category: str | None = None,
    ) -> dict | None:
        """Return a random trivia question as a dict."""
        stmt = select(TriviaQuestion).where(
            (TriviaQuestion.channel_access == user_access)
            | (TriviaQuestion.channel_access == "both")
        )
        if difficulty:
            stmt = stmt.where(TriviaQuestion.difficulty == difficulty)
        if category:
            stmt = stmt.where(TriviaQuestion.category == category)
        result = await self.session.execute(stmt)
        questions = result.scalars().all()
        if not questions:
            return None
        q = random.choice(questions)
        return {
            "id": q.id,
            "question": q.question,
            "options": json.loads(q.options),
            "correct_answer": q.correct_answer,
            "category": q.category,
            "difficulty": q.difficulty,
            "channel_access": q.channel_access,
            "lore_piece": q.lore_piece,
        }

    async def save_trivia_answer(
        self,
        user_id: int,
        question_id: int,
        answer: int,
        response_time: int | None = None,
    ) -> dict:
        """Save user answer and update statistics."""
        question = await self.session.get(TriviaQuestion, question_id)
        if not question:
            raise ValueError("Invalid question_id")
        is_correct = answer == question.correct_answer
        points = 5 if is_correct else 0
        time_bonus = 0
        if is_correct and response_time is not None:
            if response_time <= 5:
                time_bonus = 2
            elif response_time <= 10:
                time_bonus = 1
            points += time_bonus
        ans = TriviaAnswer(
            user_id=user_id,
            question_id=question_id,
            answer=answer,
            is_correct=is_correct,
            response_time=response_time,
            points_earned=points,
        )
        self.session.add(ans)
        # Update stats
        stat = await self.session.get(TriviaStat, user_id)
        if not stat:
            stat = TriviaStat(user_id=user_id)
            self.session.add(stat)
            await self.session.commit()
            await self.session.refresh(stat)
        stat.total_answered += 1
        if is_correct:
            stat.correct_answers += 1
            stat.streak += 1
            if stat.streak > stat.best_streak:
                stat.best_streak = stat.streak
            stat.total_points += points
        else:
            stat.streak = 0
        stat.last_trivia = datetime.datetime.utcnow()
        await self.session.commit()
        return {
            "is_correct": is_correct,
            "points": points,
            "lore_piece": question.lore_piece,
            "time_bonus": time_bonus,
        }

    async def get_user_trivia_stats(self, user_id: int) -> dict:
        stat = await self.session.get(TriviaStat, user_id)
        if not stat:
            return {
                "total": 0,
                "correct": 0,
                "accuracy": 0.0,
                "streak": 0,
                "best_streak": 0,
                "points": 0,
            }
        accuracy = (
            stat.correct_answers / stat.total_answered if stat.total_answered > 0 else 0.0
        )
        return {
            "total": stat.total_answered,
            "correct": stat.correct_answers,
            "accuracy": accuracy,
            "streak": stat.streak,
            "best_streak": stat.best_streak,
            "points": stat.total_points,
        }
