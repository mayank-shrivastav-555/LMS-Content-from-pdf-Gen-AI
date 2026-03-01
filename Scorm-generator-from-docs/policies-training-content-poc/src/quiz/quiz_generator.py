import random
from typing import List, Dict
import google.generativeai as genai
import time

class QuizGenerator:
    def export_quiz_json(self, file_path: str):
        """
        Export the quiz questions, options, and correct answers to a JSON file.
        """
        import json
        quiz_data = []
        for idx, (q, choices) in enumerate(zip(self.questions, self.answers)):
            correct = self.correct_choices[idx]
            quiz_data.append({
                "question": q,
                "options": choices,
                "correct_answer_index": correct,
                "correct_answer": choices[correct]
            })
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=2)
    def export_quiz(self, file_path: str):
        """
        Export the quiz questions, options, and correct answers to a text file.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            for idx, (q, choices) in enumerate(zip(self.questions, self.answers)):
                f.write(f"Q{idx+1}: {q}\n")
                for i, c in enumerate(choices):
                    f.write(f"  {i+1}. {c}\n")
                correct = self.correct_choices[idx]
                f.write(f"Correct Answer: {correct+1}. {choices[correct]}\n\n")
    def __init__(self, summary_points: List[str], num_questions: int = 5, api_key: str = None):
        self.summary_points = [p for p in summary_points if p.strip()]
        self.num_questions = min(num_questions, len(self.summary_points))
        self.questions = []
        self.answers = []
        self.correct_choices = []
        self.api_key = api_key or ''
        self.generate_quiz()

    def generate_quiz(self):
        if self.api_key:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('models/gemini-pro-latest')
            prompt = (
                "You are an expert corporate trainer. Read the following summary points and generate "
                f"{self.num_questions} multiple-choice questions (MCQs) for a quiz. "
                "Each question should be meaningful, test understanding of the content, and have only one correct answer. "
                "Provide each question with 4 options, mark the correct option, and avoid referencing slide numbers or generic phrasing. "
                "Output ONLY a valid Python list of dicts, with NO explanation, NO markdown, NO extra text. Example: "
                "[{'question': '...', 'options': ['...', '...', '...', '...'], 'answer': '...'}, ...]"
                "\nSummary points:\n" + '\n'.join(self.summary_points)
            )
            max_retries = 5
            wait_time = 70  # seconds
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(prompt)
                    import ast, json, re
                    text = response.text.strip()
                    # Try to extract the Python list from the response
                    match = re.search(r'(\[\s*{.+?}\s*\])', text, re.DOTALL)
                    if match:
                        text = match.group(1)
                    try:
                        quiz_items = ast.literal_eval(text)
                    except Exception:
                        try:
                            quiz_items = json.loads(text)
                        except Exception as e:
                            print("AI quiz generation failed, falling back to basic logic.", e)
                            self._fallback_quiz()
                            return
                    for item in quiz_items:
                        self.questions.append(item['question'])
                        self.answers.append(item['options'])
                        self.correct_choices.append(item['options'].index(item['answer']))
                    return
                except Exception as e:
                    if "quota" in str(e).lower() or "rate limit" in str(e).lower():
                        print(f"Quota error detected. Not retrying.")
                        return
                    else:
                        raise
        else:
            self._fallback_quiz()

    def _fallback_quiz(self):
        for i in range(self.num_questions):
            point = self.summary_points[i]
            keyword = ''
            if ':' in point:
                keyword = point.split(':')[0].strip()
            else:
                keyword = ' '.join(point.split()[:5])
            question = f"Q{i+1}: Which of the following best describes '{keyword}'?"
            incorrect = random.sample([p for p in self.summary_points if p != point], k=min(3, len(self.summary_points)-1))
            choices = [point] + incorrect
            random.shuffle(choices)
            self.questions.append(question)
            self.answers.append(choices)
            self.correct_choices.append(choices.index(point))

    def present_quiz(self):
        print("\nQUIZ TIME! Select the correct answer for each question:")
        user_answers = []
        for idx, (q, choices) in enumerate(zip(self.questions, self.answers)):
            print(f"\n{q}")
            for i, c in enumerate(choices):
                print(f"  {i+1}. {c}")
            ans = input("Your answer (1-4): ")
            while ans not in ['1','2','3','4']:
                ans = input("Please enter a valid option (1-4): ")
            user_answers.append(int(ans)-1)
        return user_answers

    def score_quiz(self, user_answers: List[int], passing_score: int = 60):
        correct = sum(ua == ca for ua, ca in zip(user_answers, self.correct_choices))
        total = len(self.questions)
        score = int((correct/total)*100)
        print(f"\nYour Score: {score}/{100}")
        if score >= passing_score:
            print("Result: PASS")
        else:
            print("Result: FAIL")
        print(f"Correct answers: {correct} out of {total}")
        return score
