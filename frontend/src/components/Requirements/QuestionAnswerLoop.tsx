import React, { useState } from 'react';
import { RequirementQuestion } from '@/types';
import { MessageSquare, Send, Check } from 'lucide-react';
import { format } from 'date-fns';

interface QuestionAnswerLoopProps {
  questions: RequirementQuestion[];
  onAnswer: (questionId: string, answer: string) => void;
}

export const QuestionAnswerLoop: React.FC<QuestionAnswerLoopProps> = ({
  questions,
  onAnswer,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const handleSubmit = (questionId: string) => {
    const answer = answers[questionId];
    if (answer?.trim()) {
      onAnswer(questionId, answer);
      setAnswers({ ...answers, [questionId]: '' });
    }
  };

  const unanswered = questions.filter((q) => !q.is_resolved);
  const answered = questions.filter((q) => q.is_resolved);

  return (
    <div className="space-y-6">
      {unanswered.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Pending Questions ({unanswered.length})
          </h3>
          <div className="space-y-4">
            {unanswered.map((question) => (
              <div
                key={question.id}
                className="bg-yellow-50 border border-yellow-200 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <MessageSquare className="h-5 w-5 text-yellow-600 mt-1" />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900 mb-3">
                      {question.question}
                    </p>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={answers[question.id] || ''}
                        onChange={(e) =>
                          setAnswers({
                            ...answers,
                            [question.id]: e.target.value,
                          })
                        }
                        onKeyPress={(e) =>
                          e.key === 'Enter' && handleSubmit(question.id)
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                        placeholder="Type your answer..."
                      />
                      <button
                        onClick={() => handleSubmit(question.id)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
                      >
                        <Send className="h-4 w-4" />
                        Submit
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Asked {format(new Date(question.created_at), 'PPp')}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {answered.length > 0 && (
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Answered Questions ({answered.length})
          </h3>
          <div className="space-y-4">
            {answered.map((question) => (
              <div
                key={question.id}
                className="bg-green-50 border border-green-200 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-green-600 mt-1" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 mb-2">
                      {question.question}
                    </p>
                    <p className="text-sm text-gray-700 bg-white p-2 rounded">
                      {question.answer}
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                      Answered{' '}
                      {question.answered_at &&
                        format(new Date(question.answered_at), 'PPp')}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {questions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No questions available. Run refinement to generate questions.
        </div>
      )}
    </div>
  );
};