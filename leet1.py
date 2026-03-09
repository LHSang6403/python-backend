# Given a string s, return the longest palindromic substring in s.

# Example 1:

# Input: s = "babad"
# Output: "bab"
# Explanation: "aba" is also a valid answer.
# Example 2:

# Input: s = "cbbd"
# Output: "bb"
 
# Constraints:

# 1 <= s.length <= 1000
# s consist of only digits and English letters.


class Solution:
    def extendString(self, s: str, left: int, right: int) -> str:
        while (left >= 0 and right < len(s) and s[left] == s[right]):
            left -= 1
            right += 1
        
        return s[left + 1 : right]
    
    def longestPalindrome(self, s: str) -> str:
        l = len(s)
        longest_palindrome = ""

        # Quét lần lượt từng ký tự i làm tâm đối xứng
        for i in range(l):
            # 1. Thử trường hợp chuỗi tâm LẺ (chỉ có 1 ký tự s[i] làm tâm)
            odd_palindrome = self.extendString(s, i, i)
            if len(odd_palindrome) > len(longest_palindrome):
                longest_palindrome = odd_palindrome
                
            # 2. Thử trường hợp chuỗi tâm CHẴN (nếu giống với s[i+1] làm 2 ký tự làm tâm)
            if i + 1 < l and s[i] == s[i+1]:
                even_palindrome = self.extendString(s, i, i+1)
                if len(even_palindrome) > len(longest_palindrome):
                    longest_palindrome = even_palindrome

        return longest_palindrome

solution = Solution()
print("---- res:", solution.longestPalindrome("abac"))
