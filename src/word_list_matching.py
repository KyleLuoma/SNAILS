"""
Copyright 2024 Kyle Luoma

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pandas as pd
from collections import defaultdict
import time
import Levenshtein
import math
import multiprocessing as mp

debug = False

def debug_print(*args, doprint = True):
    if debug and doprint:
        print(*args)


def main():

    nc = NaturalnessCalculator(excel_file = "./words/words_vectorized.xlsx")
    # nc = NaturalnessCalculator()

    best_candidate_dict = defaultdict(list)
    identifiers_batch_df = pd.DataFrame()
    dirty_dict = False
    do_batch = False
    batch_ix = 0

    while True:

        #Find words with same letters:
        if not do_batch:
            user_input = input("Enter a db identifier string of up to two words: ")
        else:
            try:
                user_input = identifiers_batch_df.iloc[batch_ix]["text"]
                batch_ix += 1
            except IndexError:
                print("Batch complete.")
                do_batch = False
                user_input = "save"

        if user_input == "batch":
            do_batch = True
            filename = input("enter filename of excel file with identifiers: ")
            try:
                identifiers_batch_df = pd.read_excel("./auto-scoring/" + filename + ".xlsx")
            except:
                print("File not found.")
                do_batch = False
            continue

        if user_input == "exit":
            if dirty_dict:
                filename = input("enter filename for result export:")
                filename = filename.strip().replace(".xlsx", "")
                export_df = pd.DataFrame(best_candidate_dict)
                export_df.to_excel("./words/" + filename + ".xlsx")
            break

        if user_input == "save":
            filename = input("enter filename for result export:")
            filename = filename.strip().replace(".xlsx", "")
            print(best_candidate_dict)
            export_df = pd.DataFrame(best_candidate_dict)
            export_df.to_excel("./words/" + filename + ".xlsx")
            dirty_dict = False
            best_candidate_dict = defaultdict(list)
            continue

        if user_input == "" or user_input == " " or user_input == None:
            print("No input detected.")
            continue

        tokens = nc.tokenize_identifier(user_input)
        print("Detected {} tokens: ".format(str(len(tokens))) + str(tokens) + "\n")
        start_time = time.time()

        # Use this to encode the mean score of a multi-token identifier
        
        identifier_score = 0

        for token in tokens:
            print("##### Evaluating token: " + token + " #####")
            word = token.lower()
            result = nc.evaluate_naturalness(word)

            best_match_dict = nc.get_best_match(result_dict = result)

            #Add entry to best_candidate_dict
            best_candidate_dict["identifier"].append(user_input)
            for key in best_match_dict:
                best_candidate_dict[key].append(best_match_dict[key])
            result_score = nc.score_result(best_match_dict)
            best_candidate_dict["score"].append(result_score)
            identifier_score += result_score
            dirty_dict = True

            for pair in result["pair_scores"]:
                if sum(result["pair_scores"][pair]) >= 1000000:
                    continue
                print(pair)
                print("Mean edit distance: " + str(sum(result["pair_min_distances"][pair]) / len(result["pair_min_distances"][pair])))
                print("Pair Edit distances: " + str(result["pair_min_distances"][pair]))
                print("Pair Best Candidates: " + str(result["pair_best_candidates"][pair]))
                print("Pair Second Best Candidates: " + str(result["second_best_candidates"][pair]))
                print("\n")

        for i in range(0, len(tokens)):
            best_candidate_dict["identifier_score"].append(identifier_score / len(tokens))
            best_candidate_dict["label"].append(nc.assign_label_from_score(identifier_score / len(tokens)))
 
        print("Time elapsed: " + str(time.time() - start_time))



class NaturalnessCalculator:
    """
    A class to calculate the naturalness of words and identifiers based on edit distance and ambiguity.
    Attributes:
    ----------
    word_df : pd.DataFrame
        DataFrame containing word frequency vectors.
    Methods:
    -------
    __init__(wordlist_file="./words/words", excel_file=None):
        Initializes the NaturalnessCalculator with a word list file or an Excel file.
    score_result(best_match_dict):
        Derives a score based on the edit distance and ambiguity of the best match dictionary.
    assign_label_from_score(score):
        Assigns a label based on the calculated score.
    tokenize_identifier(identifier, camel_case=True):
        Tokenizes an identifier based on camel case and delimiters.
    get_best_match(token=None, result_dict=None):
        Gets the best match for a given token or result dictionary.
    calculate_score_and_distance_of_delim_and_composite(identifier):
        Calculates the score and distance of a delimited and composite identifier.
    _mp_batch_function(identifier_sublist, mp_result_dict, p_ix):
        Batch function for multiprocessing to calculate scores and distances.
    mp_calculate_score_and_distance_of_delim_and_composite(identifier_list, num_processes=16):
        Multiprocessing function to calculate scores and distances for a list of identifiers.
    get_min_distance_for_single_word(word):
        Gets the minimum edit distance for a single word.
    distance_batch_function(word_sublist, mp_result_dict):
        Batch function for multiprocessing to get minimum distances for a list of words.
    mp_get_min_distance_for_word_list(word_list, num_processes=16):
        Multiprocessing function to get minimum distances for a list of words.
    find_most_natural_in_composite(identifier, best_score=1000000, word_list=None, score_dict=None, reparse_distance=4, min_word_len=3):
        Finds the most natural words in a composite identifier.
    evaluate_naturalness(word):
        Evaluates the naturalness of a word based on edit distances and ambiguity.
    iterate_possible_words(abbreviation):
        Iterates through possible word pairs for a given abbreviation.
    get_levenshstein_dist_dict(word, word_df):
        Gets the Levenshtein distance dictionary for a word and a DataFrame of words.
    compare_letter_order(short_word, long_word, first_letter_match=True):
        Compares the letter order of two words.
    get_words_with_letters_in_order(word, word_df):
        Gets words with letters in the same order as the given word.
    get_words_with_same_letters(word, word_df):
        Gets words with the same letters as the given word.
    create_word_letter_freq_vectors(filename="./words/words", min_word_length=3):
        Creates word letter frequency vectors from a file.
    default_value():
        Returns the default value for a dictionary.
    default_value_list():
        Returns the default list value for a dictionary.
    """

    def __init__(
            self, 
            wordlist_file = "./data/words/words", 
            excel_file = None
            ):
        if excel_file is None:
            self.word_df = self.create_word_letter_freq_vectors(wordlist_file)
        else:
            self.word_df = pd.read_excel(excel_file)



    def score_result(self, best_match_dict):
        # Derive a score as a function of the edit distance and the number of first and second best candidates described as ambiguity
        weights = {
            "MEAN_EDIT_DISTANCE": 0.4,
            "AMBIGUITY": 0.6
        }

        # Min edit distance is the single edit distance if the score is below 1000000, otherwise it is the mean edit distance of the pair
        if best_match_dict["EDIT_DIST_SINGLE"] < 1000000:
            min_edit = best_match_dict["EDIT_DIST_SINGLE"]
        else:
            min_edit = best_match_dict["MEAN_EDIT_PAIR"]

        # Raw ambiguity score is determined by the number of alternatives at lowest edit distance and lowest + 1 edit distance
        # If we are using min edit distance of the non-pair words, we use the single candidate ambiguity
        ambiguity = 0
        if min_edit == best_match_dict["EDIT_DIST_SINGLE"]:
            ambiguity = (
                best_match_dict["CT_BEST_SINGLE"] +
                best_match_dict["CT_SECONDBEST_SINGLE"]
            )
        else:
            ambiguity = (
                best_match_dict["W1_BEST_CT"] + 
                best_match_dict["W1_SEC_BEST_CT"] +
                best_match_dict["W2_BEST_CT"] +
                best_match_dict["W2_SEC_BEST_CT"]
            )

        # Calculate the score
        score = (
            weights["MEAN_EDIT_DISTANCE"] * (1 / (min_edit + 1)) +
            weights["AMBIGUITY"] * (1 / max(math.log(1 + ambiguity, 2), 1))
        )

        return score


        
    def assign_label_from_score(self, score):
        label_mins = {
            "N1": 0.55,
            "N2": 0.30,
            "N3": 0.0,
        }
        for label in label_mins:
            if score >= label_mins[label]:
                return label



    def tokenize_identifier(self, identifier, camel_case = True):
        #Split on camel case:
        identifer = identifier.strip()
        token_indexes = [0]
        if camel_case:
            for i in range(1, len(identifier)):
                if identifier[i].isupper() and identifier[i - 1].islower():
                    token_indexes.append(i)
        token_indexes.append(len(identifier))
        tokens = []
        for i in range(len(token_indexes) - 1):
            tokens.append(identifier[token_indexes[i]:token_indexes[i + 1]])
        identifier = " ".join(tokens)
        #Split on delimiters:
        delimiters = ["_", "-", " ", "(", ")", "[", "]", "{", "}", "<", ">", "/", "\\", "|", ":", ";", ",", ".", "?", "!", "@", "#", "$", "%", "^", "&", "*", "~", "`", "+", "=", "\"", "'"]
        for delimiter in delimiters:
            identifier = identifier.replace(delimiter, " ")
        tokens = identifier.split(" ")
        tokens = [token for token in tokens if token != ""]
        return tokens
    


    def get_best_match(self, token = None, result_dict = None):
        if result_dict is None and token is not None:
            result_dict = self.evaluate_naturalness(token)

        if token is None and result_dict is not None:
            token = result_dict["token"]
            print(token)

        if token is None and result_dict is None:
            raise ValueError("Either token or result_dict must be provided.")

        export_dict = {
            "token": "",
            "EDIT_DIST_SINGLE": -1,
            "CT_BEST_SINGLE": -1,
            "CT_SECONDBEST_SINGLE": -1,
            "BEST_PAIR": (),
            "MEAN_EDIT_PAIR": -1,
            "W1_EDIT": -1,
            "W2_EDIT": -1,
            "W1_BEST_CT": -1,
            "W1_SEC_BEST_CT": -1,
            "W2_BEST_CT": -1,
            "W2_SEC_BEST_CT": -1
        }
        export_dict["token"] = token
        export_dict["EDIT_DIST_SINGLE"] = result_dict["pair_min_distances"][("", token)][0]
        export_dict["CT_BEST_SINGLE"] = len(result_dict["pair_best_candidates"][("", token)][0])
        export_dict["CT_SECONDBEST_SINGLE"] = len(result_dict["second_best_candidates"][("", token)][0])

        best_min_mean = 1000000
        best_pair = ("", token)

        for pair in result_dict["pair_scores"]:
            mean = sum(result_dict["pair_min_distances"][pair]) / len(result_dict["pair_min_distances"][pair])
            if mean < best_min_mean:
                best_min_mean = mean
                best_pair = pair
        
        export_dict["BEST_PAIR"] = best_pair
        export_dict["MEAN_EDIT_PAIR"] = best_min_mean
        export_dict["W1_EDIT"] = result_dict["pair_min_distances"][best_pair][0]
        export_dict["W1_BEST_CT"] = len(result_dict["pair_best_candidates"][best_pair][0])
        export_dict["W1_SEC_BEST_CT"] = len(result_dict["second_best_candidates"][best_pair][0])

        if len(result_dict["pair_min_distances"][best_pair]) > 1:
            export_dict["W2_EDIT"] = result_dict["pair_min_distances"][best_pair][1]
            export_dict["W2_BEST_CT"] = len(result_dict["pair_best_candidates"][best_pair][1])
            export_dict["W2_SEC_BEST_CT"] = len(result_dict["second_best_candidates"][best_pair][1])

        return export_dict
    


    def calculate_score_and_distance_of_delim_and_composite(
            self, 
            identifier: str
            ) -> tuple[list, dict]:
        word_list = self.tokenize_identifier(identifier)
        all_scores = {}
        all_words = []
        for word in word_list:
            words, scores = self.find_most_natural_in_composite(word.lower())
            all_words += words
            for score in scores:
                all_scores[score] = scores[score]
        return all_words, all_scores
    


    def _mp_batch_function(
            self,
            identifier_sublist,
            mp_result_dict,
            p_ix
    ) -> None:
        for ix, identifier in enumerate(identifier_sublist):
            words, scores = self.calculate_score_and_distance_of_delim_and_composite(
                identifier
            )
            mp_result_dict[identifier] = scores
    


    def mp_calculate_score_and_distance_of_delim_and_composite(
            self,
            identifier_list: str,
            num_processes = 16
            ) -> dict:
        mp_function = self._mp_batch_function
        sublists = [[] for i in range(0, num_processes)]
        for ix, identifier in enumerate(identifier_list):
            sublists[ix % num_processes].append(identifier)
        print(sublists)
        manager = mp.Manager()
        process_results = [
            manager.dict() for i in range(0, num_processes)
        ]
        manager.dict()
        processes = []
        for p_ix in range(0, num_processes):
            processes.append(
                mp.Process(
                    target=mp_function,
                    args=(
                        sublists[p_ix],
                        process_results[p_ix],
                        p_ix
                    )
                )
            )
        for p_ix, p in enumerate(processes):
            print("Starting process", p_ix)
            p.start()
        for p in processes:
            print("Ending process", p)
            p.join()
        ident_list = []
        for ident_dict in process_results:
            for ident in ident_dict:
                ident_list.append(ident)
        return ident_list



    def get_min_distance_for_single_word(self, word: str):
        letter_filtered = self.get_words_with_same_letters(word, self.word_df)
        order_filtered = self.get_words_with_letters_in_order(word, letter_filtered)
        l_distances, stats_dict = self.get_levenshstein_dist_dict(word, order_filtered)
        if len(l_distances) == 0:
            l_distances, stats_dict = self.get_levenshstein_dist_dict(word, letter_filtered)
        if len(l_distances.keys()) > 0:
            return min(l_distances.keys())
        else:
            return -1
        



    def distance_batch_function(self, word_sublist, mp_result_dict):
        for word in word_sublist:
            if len(word) > 0:
                distance = self.get_min_distance_for_single_word(word)
            else:
                distance = -1
            mp_result_dict[word] = distance




    def mp_get_min_distance_for_word_list(self, word_list: list, num_processes: int = 16):

        sublists = [[] for i in range(0, num_processes)]
        for ix, identifier in enumerate(word_list):
            sublists[ix % num_processes].append(identifier)
        manager = mp.Manager()
        process_results = [
            manager.dict() for i in range(0, num_processes)
        ]
        processes = []
        for p_ix in range(0, num_processes):
            processes.append(
                mp.Process(
                    target=self.distance_batch_function,
                    args=(
                        sublists[p_ix],
                        process_results[p_ix]
                    )
                )
            )
        for p_ix, p in enumerate(processes):
            print("Starting process", p)
            p.start()
        for p in processes:
            print("Ending process", p)
            p.join()
        all_results_dict = {}
        for ident_dict in process_results:
            for ident in ident_dict:
                all_results_dict[ident] = ident_dict[ident]
        return all_results_dict



    def find_most_natural_in_composite(
            self,
            identifier: str, 
            best_score: int = 1000000, 
            word_list: list = None, 
            score_dict: dict = None,
            reparse_distance = 4, 
            min_word_len = 3
        ) -> tuple[list, dict]:
        if word_list == None:
            word_list = []
        if score_dict == None:
            score_dict = {}
        if len(identifier) <= 3:
            result_df = self.get_words_with_same_letters(identifier, self.word_df)
            result_df = self.get_words_with_letters_in_order(identifier, result_df)
            l_distances, stats_dict = self.get_levenshstein_dist_dict(identifier, result_df)
            if len(l_distances.keys()) > 0:
                l_distance = min(l_distances.keys())
            else:
                l_distance = 999999
            return [identifier], {identifier: {"distance": l_distance, "possible_word_count": len(l_distances[l_distance])}}
        pair_candidates = self.iterate_possible_words(identifier)
        pair_scores = []
        best_score = 2000000
        best_possibilities = 2000000
        p0_l_distances = defaultdict(int)
        p1_l_distances = defaultdict(int)
        # Iterate through all pair candidates to find the best (lowest) distance for both pairs combined
        for p in pair_candidates:
            p0_distance = 1000000
            p0_possibilities = 1000000
            # First check the pairs where the entire word is evaluated
            if p[0] == "":
                result_df = self.get_words_with_same_letters(p[1], self.word_df)
                result_df = self.get_words_with_letters_in_order(p[1], result_df)
                l_distances, stats_dict = self.get_levenshstein_dist_dict(p[1], result_df)
                if len(l_distances) > 0 and min(l_distances.keys()) < reparse_distance:
                    l_dist = min(l_distances.keys())
                    if p[1] not in word_list:
                        return [p[1]], {p[1]: {"distance": l_dist, "possible_word_count": len(l_distances[l_dist])}}
                    else:
                        return ([], {})
                
            # Find the min score for the left word
            if p[0] != "":
                result_df = self.get_words_with_same_letters(p[0], self.word_df)
                result_df = self.get_words_with_letters_in_order(p[0], result_df)
                p0_l_distances, stats_dict = self.get_levenshstein_dist_dict(p[0], result_df)
                if len(p0_l_distances) > 0:
                    p0_distance = min(p0_l_distances.keys())  
                    p0_possibilities = len(p0_l_distances[p0_distance])   
            
            p1_distance = 1000000
            p1_possibilities = 1000000
            # Find the min score for the right word
            if p[1] != "":
                result_df = self.get_words_with_same_letters(p[1], self.word_df)
                result_df = self.get_words_with_letters_in_order(p[1], result_df)
                p1_l_distances, stats_dict = self.get_levenshstein_dist_dict(p[1], result_df)
                if len(p1_l_distances) > 0:
                    p1_distance = min(p1_l_distances.keys())
                    p1_possibilities = len(p1_l_distances[p1_distance])
            # Combined score to evaluate the pair
            score = p0_distance + p1_distance
            possibilities = p0_possibilities + p1_possibilities
            if score < best_score and possibilities < best_possibilities:
                best_score = score
                best_possibilities = possibilities
            pair_scores.append((p0_distance, p1_distance, score, p0_possibilities, p1_possibilities))
        # Create a list of the lowest scoring pairs
        best_pairs = []
        best_scores = []
        for ix, pair in enumerate(pair_candidates):
            if pair_scores[ix][2] == best_score:
                best_pairs.append(pair)
                best_scores.append(pair_scores[ix])
        # Check if any words are below the reparse distance threshold (they are good enough)
        # and find the best pair.
        p0_longest = 0
        p0_longest_ix = -1
        p1_longest = 0
        p1_longest_ix = -1
        for ix, p in enumerate(best_pairs):
            if best_scores[ix][0] < reparse_distance and len(p[0]) > p0_longest:
                p0_longest = len(p[0])
                p0_longest_ix = ix
            if best_scores[ix][1] < reparse_distance and len(p[1]) > p1_longest:
                p1_longest = len(p[0])
                p1_longest_ix = ix

        if p0_longest_ix >= 0:
            word_list.append(best_pairs[p0_longest_ix][0])
            score_dict[best_pairs[p0_longest_ix][0]] = {
                "distance": best_scores[p0_longest_ix][0],
                "possible_word_count": best_scores[p0_longest_ix][3]
            }
            new_words, new_scores = self.find_most_natural_in_composite(
                best_pairs[p0_longest_ix][1], 
                word_list=word_list,
                score_dict=score_dict
                )
            for word in new_words:
                if word not in word_list:
                    word_list.append(word)
            for score in new_scores:
                score_dict[score] = new_scores[score]
            return word_list, score_dict
        else:
            new_words, new_scores = self.find_most_natural_in_composite(
                best_pairs[p0_longest_ix][0], 
                word_list=word_list,
                score_dict=score_dict
                )
            for word in new_words:
                if word not in word_list:
                    word_list.append(word)
            for score in new_scores:
                score_dict[score] = new_scores[score]

        if p1_longest_ix >= 0:
            word_list.append(best_pairs[p1_longest_ix][1])
            score_dict[best_pairs[p1_longest_ix][1]] = {
                "distance": best_scores[p1_longest_ix][1],
                "possible_word_count": best_scores[p1_longest_ix][4]
            }
            new_words, new_scores = self.find_most_natural_in_composite(
                best_pairs[p1_longest_ix][0], 
                word_list=word_list,
                score_dict=score_dict
                )
            for word in new_words:
                if word not in word_list:
                    word_list.append(word)
            for score in new_scores:
                score_dict[score] = new_scores[score]
            return word_list, score_dict
        else:
            new_words, new_scores = self.find_most_natural_in_composite(
                best_pairs[p1_longest_ix][1], 
                word_list=word_list,
                score_dict=score_dict
                )
            for word in new_words:
                if word not in word_list:
                    word_list.append(word)
            for score in new_scores:
                score_dict[score] = new_scores[score]

        return word_list, score_dict



    def evaluate_naturalness(self, word):
        original_token = word
        word_pairs = self.iterate_possible_words(word)
        pair_scores = defaultdict(self.default_value_list)
        pair_counts = defaultdict(self.default_value_list)
        pair_means = defaultdict(self.default_value_list)
        pair_min_distances = defaultdict(self.default_value_list)
        l_distances = defaultdict(self.default_value_list)
        pair_best_candidates = defaultdict(self.default_value_list)
        second_best_candidates = defaultdict(self.default_value_list)

        for pair in word_pairs:
            for word in pair:
                if word == "":
                    pair_scores[pair].append(1)
                    pair_counts[pair].append(1)
                    pair_means[pair].append(1)
                    continue
                result_df = self.get_words_with_same_letters(word, self.word_df)
                result_df = self.get_words_with_letters_in_order(word, result_df)
                l_distances, stats_dict = self.get_levenshstein_dist_dict(word, result_df)

                if len(l_distances) > 0:
                    pair_scores[pair].append(stats_dict["total_distance"])
                    pair_counts[pair].append(stats_dict["count_words"])
                    pair_means[pair].append(stats_dict["average_distance"])
                    pair_min_distances[pair].append(stats_dict["min_distance"])
                    pair_best_candidates[pair].append(l_distances[stats_dict["min_distance"]])
                    second_best_candidates[pair].append(l_distances[stats_dict["min_distance"] + 1])
                else:
                    pair_scores[pair].append(1000000)
                    pair_counts[pair].append(1000000)
                    pair_means[pair].append(1000000)
                    pair_min_distances[pair].append(1000000)
                    pair_best_candidates[pair].append([])
                    second_best_candidates[pair].append([])

        return {
            "token": original_token,
            "pair_scores": pair_scores,
            "pair_counts": pair_counts,
            "pair_means": pair_means,
            "pair_min_distances": pair_min_distances,
            "pair_best_candidates": pair_best_candidates,
            "second_best_candidates": second_best_candidates
        }


    def iterate_possible_words(self, abbreviation):
        word_pairs = []
        for i in range(0, len(abbreviation)):
            word1 = abbreviation[0:i]
            word2 = abbreviation[i:len(abbreviation)]
            word_pairs.append((word1, word2))
        return word_pairs



    def get_levenshstein_dist_dict(self, word, word_df):

        stats_dict = defaultdict(self.default_value)
        result_dict = defaultdict(self.default_value_list)
        total_distance = 0
        stats_dict["min_distance"] = 1000000

        for row in word_df.itertuples():
            distance = Levenshtein.distance(str(word), str(row.word))
            stats_dict["total_distance"] += distance
            stats_dict["count_words"] += 1
            total_distance += distance
            result_dict[distance].append(row.word)
            if distance < stats_dict["min_distance"]:
                stats_dict["min_distance"] = distance

        if stats_dict["count_words"] > 0:
            stats_dict["average_distance"] = total_distance / stats_dict["count_words"]
        else:
            stats_dict["average_distance"] = 0
        return result_dict, stats_dict



    def compare_letter_order(self, short_word, long_word, first_letter_match = True):

        do_debug_print = False

        if short_word == long_word:
            return True
        
        if first_letter_match and short_word[0] != long_word[0]:
            return False

        s_ix = 0
        l_ix = 0
        s_let = ""
        l_let = ""

        while s_ix < len(short_word) and l_ix < len(long_word):
            l_let = long_word[l_ix]
            s_let = short_word[s_ix]
            
            if s_let == l_let:
                s_ix += 1
                l_ix += 1
            else:
                l_ix += 1

        
        debug_print("s_ix: " + str(s_ix), doprint = do_debug_print)
        debug_print("l_ix: " + str(l_ix), doprint = do_debug_print)

        # Are we at the end of both words? And do the letters match?
        if (
            s_ix == len(short_word) - 1 
            and l_ix == len(long_word) - 1
        ):
            if s_let == l_let:
                debug_print("Letters at end of word match and letters are in order.", doprint = do_debug_print)
                return True
            else:
                debug_print("Letters at end of word do not match.", doprint = do_debug_print)
                return False
            
        if (
            l_ix == len(long_word) 
            and s_ix < len(short_word)
        ):
            debug_print("Reached end of long word before end of short word.", doprint = do_debug_print)
            return False
        debug_print("Reached end of short word before end of long word.", doprint = do_debug_print)
        return True



    def get_words_with_letters_in_order(self, word, word_df):
        debug_print("Word: " + word)
        result_df = word_df[word_df.apply(
                lambda row: self.compare_letter_order(word, str(row["word"])),
                axis=1
            )]
        return result_df

        

    def get_words_with_same_letters(self, word, word_df):
        result_df = word_df

        letter_freqs = defaultdict(self.default_value)
        for letter in word:
            letter_freqs[letter] += 1

        for letter in letter_freqs:
            try:
                result_df = result_df[result_df[letter] >= letter_freqs[letter]]
            except KeyError:
                pass
        return result_df


    def create_word_letter_freq_vectors(self, filename = "./words/words", min_word_length = 3):
        f = open(filename, "r")
        words_raw = f.readlines()
        f.close()

        words_raw = [word.strip() for word in words_raw]
        words = [word for word in words_raw if len(word) >= min_word_length]

        additional_words = ["lookup", "lookups", "transect", "transects"]
        words.extend(additional_words)

        alphabet = "abcdefghijklmnopqrstuvwxyz"
        alphabet += "0123456789"

        word_letter_counts  = [[] for i in range(len(alphabet))]

        print("Initializing letter count matrix...")
        for i in range(0, len(words)):
            for j in range(0, len(alphabet)):
                word_letter_counts[j].append(0)
        print("Letter count matrix initialized.")

        print("Vectorizing words letter counts...")
        for ix, word in enumerate(words):
            word = word.lower()
            for w_letter in word:
                if w_letter not in alphabet:
                    continue
                letter_ix = alphabet.index(w_letter)
                word_letter_counts[letter_ix][ix] += 1

        print("Vectorization complete.")

        df_dict = {letter: word_letter_counts[ix] for ix, letter in enumerate(alphabet)}
        df_dict["word"] = words

        print("Creating dataframe...")
        df = pd.DataFrame(
            df_dict
        )
        df.to_excel("./data/words/words_vectorized.xlsx")
        return df


    def default_value(self):
        return 0


    def default_value_list(self):
        return []
    


if __name__ == "__main__":
    main()
    # batch_test()
