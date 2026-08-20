# <img src="web/src/assets/favicon.svg" height=30> Last Translation Benchmark

> **Abstract:**
> To make progress in any task with AI, we need benchmarks that test the frontier of capabilities in that task, and evaluation methods that inform us about failure cases.
> Standard translation benchmarks are often either trivial (having few authentic mistakes) or unrealistic (overly synthetically contrived).
> Furthermore, automatic translation metrics can be hijacked, are not reliable, and the output is not interpretable with high confidence.
> Even gold human evaluation is not problem-free: it often lacks reproducibility, objectivity, and scalability.
> This prevents us from tracking objective progress in the field and from informing where we should focus next.
> We introduce the Last Translation Benchmark, which contains human-authored inputs (texts, images, audio, videos) which break state-of-the-art machine translation models across many language pairs.
> Each input is peer-reviewed and also paired with one or more handcrafted verification rules, which allow for reproducible objective evaluation of future models under the same conditions.
> The Last Translation Benchmark is a live dataset that accepts contributions.
> The latest version is `LTBv1`, containing accepted contributions up to September 1st 2026, with future releases planned with subsequent contributions.

This repository contains the technical backend for the online platform as well as analysis scripts for the Last Translation Benchmark paper (upcoming) and data (upcoming).
If you're interested in contributing, register at [last-translation-benchmark.vilda.net](https://last-translation-benchmark.vilda.net) and make sure to read the instructions beforehand.
With 10 approved submissions, contributors are offered data co-authorship.

<!-- <img width="1000" alt="Last Translation Benchmark poster" src="https://github.com/user-attachments/assets/f0971f5c-fc95-4d48-9f13-a01934b4913d" /> -->

## Data

TODO: Upcoming

> Example from English to Czech translation: \
> **Source**: "_what's the difference between jail and prison?_" \
> **Translation (Google Translate)**: "_jaký je rozdíl mezi vězením a vězením?_" \
> **Translation (Human)**: "_jaký je rozdíl mezi vazební věznicí a vězením?_" \
> **Verification rule**: "_The words for the "jail" and "prison" shouldn't be identical."_


## Development

```bash
# requires python >=3.12, node >= 20
npm install --prefix web
npm run build --prefix web/
# use this one when developing
pip install -e ".[dev]" && pre-commit install -c .github/.pre-commit-config.yaml
# use this one when not developing
pip install -e .
# prints login URLs
python3 server
```

The `server/` contains source code for the server.
The `web/` is the frontend code (TypeScript) which, when built, goes to `server/static/` to be served by the server.

You can specify the `--host`, `--port` and `--host-public` arguments when starting the server. 
The last is used to show the login URLs.
For management of environment variables, create `config.toml` based on `config.template.toml`.
The instructions in [web/src/assets/instructions.html](web/src/assets/instructions.html) are based on upstream document written in Typst and should not be edited locally in this repo.

## License

The source code in this repository is licensed under [MIT](LICENSE), and the data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.en).

## Contributing

We welcome bugreports, hands-on, and research contributions.
AI-generated PRs are fine as long as you verify everything and take ownership of the changes.
This effort is organized by a collective of researchers from ETH Zurich, JHU, KIT, UvA, CUNI, and many others.
Reach out to [last-translation-benchmark@vilda.net](mailto:last-translation-benchmark@vilda.net) with inquiries.
Please do not reach out about the status of your pending submissions.
To speed up the review process, you can invite other speakers of your languages who can review your submissions or nominate yourself to be a reviewer.

## Citation

The Last Translation Benchmark is still in preparation.
If you need to cite this project, please use this temporary BibTeX:
```bibtex
@misc{last-translation-benchmark,
title={Last Translation Benchmark},
author={Vilém Zouhar and Niyati Bafna and Maike Züfle and Mukund Choudhary and Sara Rajaee and Pinzhen Chen and Jannis Vamvas and Sara Papi and Ona de Gibert and Patrícia Schmidtová and Leshem Choshen and Gabriele Sarti and Bhavitvya Malik and Orfeas Menis Mastromichalakis and Michelle Wastl and Jan Niehues and Rico Sennrich and Alon Lavie and Mrinmaya Sachan and Ondřej Bojar and Jörg Tiedemann and Alham Fikri Aji and Sowmya Vajjala and Chalamalasetti Kranti and Hend Al-Khalifa and Cristina España-Bonet and David Kaczér and Daban Q. Jaff and Malik Marmonier and Nils Rehlinger and Juan Daniel Cuervo Villa and Shunta Asano and Manuel Tuor and Vaisakhi Mishra and Dominik Macháček and Jagannathan Ramanujam and Jonathan Tonglet and Pouya Sadeghi and Andrés Jerez and Maria Lymperaiou and Fred Philippy and Fabian Retkowski and Zuzana Nadova and Avantica Vempati and Ron Keinan and Maria Carmen Staiano and Arafat Ahsan and Reem Alzahrani and Adrian Cosma and Vitalii Babenko and Fatima Haouari and Bo Chen and Aviral Nigam and Wafa Aissa and Venkata Prasanth Kumar Gummadi and Shuaib Shuaib Yusuf and Jean Maillard and Kaustubh Dhole and Heejin Do and Hanna Yukhymenko and Zhengxiang Wang and Lukas Edman and Kaiser Sun and Bowen Yi and Eliya Habba and Sangwon Ryu and Dipankar Srirag and Shaomu Tan and Antonia Karamolegkou and Javier García Gilabert and Valentin Scourneau and Ruta Binkyte and Manar Ali and Koel Dutta Chowdhury and Silvia Casola and Yihong Liu and Giuseppe Gallipoli and Amir Hossein Yari and Ana-Maria Bucur and Vatsal Venkatkrishna and Philipp Mondorf and Daryna Dementieva and Christian Hoang and Ritwik Tiwari and Sina Ahmadi and Saugata Purkayastha and Manon Reusens and Fida Mohammad Thoker and Enzo Doyen and Sergey Troshin and Lance Calvin Lim Gamboa and Cojocaru Nicoleta and David Africa and Xiaochuang Yuan and Mike Zhang and Farzad Shami and Anumit Garg and Vladislav Poritski and Yi Fan and Linh Vu and Kazuki Egashira and Natchapon Jongwiriyanurak and Marius Huber and Hassan Soliman and Badal Nyalang and Beni Egressy and Sukannya Purkayastha and Paul Gavrikov and Sunisth Kumar and R. Damanhuri and Kamile Dementaviciute and Deokhyung Kang and Raoyuan Zhao and Karen Sanchez and Terry Jingchen Zhang and Roman Wixinger and Priyaranjan Pattnayak and Mateusz Lango and Hongbin Na and Emilian Radoi and Chenyi Zhao and Carlos Hinojosa and Ashok Urlana and Andrianos Michail and Andrea Gregor de Varda and Rayyan Merchant and Mohammad Sadegh Gholizadeh and Vivek Harsha Lakkamaneni and Sophia Conrad and Shubhashis Roy Dipta and Samuel Frontull and Rishit Dagli and Ngoc Quynh Tram Do and Luis Lara and Jan Kocoń and Francesca Padovani and Fidel Rodríguez Velásquez and Antoine Taroni and Anmol Goel and Mykola Haltiuk and Joy Olusanya and Tommaso Cerruti and Jimson Paulo Layacan and Beatrice Savoldi and Rachel Bawden and Theresia Veronika Rampisela and Sankalan Pal Chowdhury and Harris Abdul Majid and Elias Herranen and Wei Liu and Thura Aung and Sharifa Djurabaeva and Pavel Stepachev and Marco Gaido and Lena Libon and Kenneth Enevoldsen and Htet Kaung San and Gergo Ignacz and Dzmitry Kuzmin and Deep Shah and Abdulaziz Nura Kani and Tosin Adewumi and Jirui Qi and Alex Flückiger and Tim Graf and Luis Frentzen Salim and Yurii Paniv and Yolanda Xavier and Shree Harsha Bokkahalli Satish and Raia Abu Ahmad and Papa Abdou Karim Karou Diallo and Minh Ngọc and Marii Ojastu and Joseph Attieh and Jenny Chim and Francesco Pinto and Benoît Sagot and Ayush Sunil Munot and Marek Šuppa and Jingwei Ni and Yu Fan},
year={2026},
url={https://last-translation-benchmark.vilda.net/},
note={In preparation},
}
```